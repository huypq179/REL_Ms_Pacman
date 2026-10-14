"""
Explainability Module - Attention, Grad-CAM, Saliency, Q-value Analysis
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional, Any
import cv2


class AttentionVisualizer:
    """Visualize attention mechanisms."""
    
    def __init__(self, num_heads: int = 3):
        self.num_heads = num_heads
        self.attention_history = []
    
    def process_attention_maps(
        self, 
        attention_maps: list, 
        frame_shape: Tuple[int, int] = (84, 84)
    ) -> Dict[str, np.ndarray]:
        """Process attention maps for visualization."""
        
        processed = {}
        
        for i, attn_map in enumerate(attention_maps):
            # Convert to numpy
            if isinstance(attn_map, torch.Tensor):
                attn_np = attn_map.detach().cpu().numpy()
            else:
                attn_np = attn_map
            
            # Handle batch dimension
            if attn_np.ndim == 4:
                attn_np = attn_np[0]  # Take first element of batch
            
            # Squeeze channel dimension
            if attn_np.ndim == 3:
                attn_np = attn_np.squeeze(0)
            
            # Normalize to [0, 1]
            attn_np = (attn_np - attn_np.min()) / (attn_np.max() - attn_np.min() + 1e-8)
            
            # Resize to frame shape
            attn_resized = cv2.resize(attn_np, (frame_shape[1], frame_shape[0]))
            
            processed[f'head_{i}'] = attn_resized
        
        return processed
    
    def apply_attention_overlay(
        self,
        frame: np.ndarray,
        attention_map: np.ndarray,
        alpha: float = 0.3,
        colormap: str = 'hot'
    ) -> np.ndarray:
        """Apply attention heatmap overlay to frame."""
        
        # Ensure frame is uint8
        if frame.dtype != np.uint8:
            frame = (frame * 255).astype(np.uint8)
        
        # Apply colormap
        if colormap == 'hot':
            heatmap = cv2.applyColorMap(
                (attention_map * 255).astype(np.uint8), 
                cv2.COLORMAP_HOT
            )
        elif colormap == 'viridis':
            heatmap = cv2.applyColorMap(
                (attention_map * 255).astype(np.uint8), 
                cv2.COLORMAP_VIRIDIS
            )
        else:
            heatmap = cv2.applyColorMap(
                (attention_map * 255).astype(np.uint8), 
                cv2.COLORMAP_JET
            )
        
        # Blend
        overlay = cv2.addWeighted(frame, 1 - alpha, heatmap, alpha, 0)
        
        return overlay


class GradCAMExplainer:
    """Grad-CAM for CNN feature visualization."""
    
    def __init__(self, model, target_layer_name: str = "backbone"):
        self.model = model
        self.target_layer_name = target_layer_name
        self.gradients = None
        self.activations = None
        
        # Register hook
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward/backward hooks."""
        
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        # Find target layer
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                module.register_forward_hook(forward_hook)
                module.register_backward_hook(backward_hook)
    
    def explain(
        self, 
        input_tensor: torch.Tensor,
        target_action: Optional[int] = None
    ) -> np.ndarray:
        """Generate Grad-CAM visualization."""
        
        input_tensor.requires_grad_(True)
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Backward pass
        if target_action is not None:
            target_score = output[0, target_action]
        else:
            target_score = output.max()
        
        self.model.zero_grad()
        target_score.backward()
        
        # Compute Grad-CAM
        if self.gradients is None or self.activations is None:
            return None
        
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        
        # Normalize
        cam = cam[0, 0]  # Remove batch and channel dims
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        
        return cam.detach().cpu().numpy()


class SaliencyExplainer:
    """Saliency map computation."""
    
    @staticmethod
    def compute_saliency(
        input_tensor: torch.Tensor,
        model,
        target_action: Optional[int] = None
    ) -> np.ndarray:
        """Compute saliency map using input gradients."""
        
        input_tensor.requires_grad_(True)
        
        # Forward pass
        output = model(input_tensor)
        
        # Select target
        if target_action is not None:
            score = output[0, target_action]
        else:
            score = output.max()
        
        # Backward pass
        score.backward()
        
        # Get gradients
        gradients = input_tensor.grad.data.abs()
        gradients = gradients.max(dim=1, keepdim=True)[0]  # Max across channels
        
        # Normalize
        saliency = gradients[0, 0]  # Remove batch and channel dims
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
        
        return saliency.detach().cpu().numpy()


class QValueAnalyzer:
    """Analyze Q-values and action predictions."""
    
    def __init__(self, num_actions: int = 9):
        self.num_actions = num_actions
        self.action_names = {
            0: "NOOP",
            1: "UP",
            2: "RIGHT",
            3: "LEFT",
            4: "DOWN",
        }
    
    def analyze_qvalues(
        self,
        q_values: torch.Tensor,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """Analyze Q-values."""
        
        if isinstance(q_values, torch.Tensor):
            q_np = q_values.detach().cpu().numpy()
        else:
            q_np = q_values
        
        q_np = q_np.squeeze()
        
        analysis = {
            'q_values': q_np,
            'best_action': int(np.argmax(q_np)),
            'best_q_value': float(np.max(q_np)),
            'q_value_spread': float(np.std(q_np)),
            'action_probabilities': self._softmax(q_np, temperature),
        }
        
        return analysis
    
    @staticmethod
    def _softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Compute softmax with temperature."""
        e_x = np.exp((x - np.max(x)) / temperature)
        return e_x / e_x.sum()
    
    def get_action_explanation(self, q_values: torch.Tensor) -> str:
        """Generate natural language explanation of action choice."""
        
        analysis = self.analyze_qvalues(q_values)
        best_action = analysis['best_action']
        best_q_value = analysis['best_q_value']
        q_vals = analysis['q_values']
        
        action_name = self.action_names.get(best_action, f"ACTION_{best_action}")
        
        # Find second best
        sorted_indices = np.argsort(-q_vals)
        second_best_action = sorted_indices[1]
        second_best_value = q_vals[second_best_action]
        
        margin = best_q_value - second_best_value
        
        if margin < 0.1:
            confidence = "uncertain (low margin)"
        elif margin < 0.5:
            confidence = "moderately confident"
        else:
            confidence = "confident"
        
        explanation = f"Choose {action_name} (Q={best_q_value:.2f}, {confidence})"
        
        return explanation


class ExplainabilityEngine:
    """Complete explainability pipeline."""
    
    def __init__(self, model, num_actions: int = 9):
        self.model = model
        self.num_actions = num_actions
        
        self.attention_viz = AttentionVisualizer(num_heads=3)
        self.gradcam = GradCAMExplainer(model)
        self.saliency = SaliencyExplainer()
        self.qvalue_analyzer = QValueAnalyzer(num_actions)
    
    def explain_decision(
        self,
        observation: np.ndarray,
        return_visualizations: bool = True
    ) -> Dict[str, Any]:
        """Comprehensive explanation of agent decision."""
        
        # Convert to tensor
        if isinstance(observation, np.ndarray):
            obs_tensor = torch.from_numpy(observation).float()
            if obs_tensor.ndim == 3:
                obs_tensor = obs_tensor.unsqueeze(0)
        else:
            obs_tensor = observation
        
        # Q-value analysis
        with torch.no_grad():
            q_values = self.model(obs_tensor)
        
        qvalue_analysis = self.qvalue_analyzer.analyze_qvalues(q_values)
        action_explanation = self.qvalue_analyzer.get_action_explanation(q_values)
        
        # Attention maps
        attention_data = self.model.get_explanations()
        
        explanation = {
            'q_values': qvalue_analysis,
            'action_explanation': action_explanation,
            'attention': attention_data,
        }
        
        if return_visualizations:
            # Grad-CAM
            try:
                gradcam_map = self.gradcam.explain(obs_tensor, qvalue_analysis['best_action'])
                explanation['gradcam'] = gradcam_map
            except:
                explanation['gradcam'] = None
            
            # Saliency
            try:
                saliency_map = self.saliency.compute_saliency(
                    obs_tensor, 
                    self.model, 
                    qvalue_analysis['best_action']
                )
                explanation['saliency'] = saliency_map
            except:
                explanation['saliency'] = None
        
        return explanation


if __name__ == "__main__":
    print("Explainability module loaded successfully!")
