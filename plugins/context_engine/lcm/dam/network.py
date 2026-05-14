"""Dense Associative Memory network -- implements the paper's bipartite architecture.

Reference: "Biologically Plausible Dense Associative Memory with Exponential Capacity"
arxiv 2601.00984v2
"""
import numpy as np
from typing import Any


class DenseAssociativeMemory:
    """Two-layer bipartite network with exponential storage capacity.

    Nv visible neurons, Nh hidden neurons. Weight matrix xi: (Nv, Nh).
    Theoretical capacity: 2^Nh patterns when Nv >> Nh.
    """

    def __init__(self, nv: int = 2048, nh: int = 64, theta: float = 0.5,
                 beta: float = 10.0, lr: float = 0.005):
        self.nv = nv
        self.nh = nh
        self.theta = theta
        self.beta = beta  # Sigmoid sharpness for training
        self.lr = lr
        self.n_patterns_trained = 0

        # Xavier initialization
        scale = np.sqrt(2.0 / (nv + nh))
        self.xi = (np.random.randn(nv, nh) * scale).astype(np.float32)

    def get_hidden_activations(self, v: np.ndarray) -> np.ndarray:
        """Compute binary hidden activations: s = Theta(sqrt(Nh)/Nv * xi^T * v - theta)"""
        h = (np.sqrt(self.nh) / self.nv) * (self.xi.T @ v)
        return (h >= self.theta).astype(np.float32)

    def _sigmoid_hidden(self, v: np.ndarray) -> np.ndarray:
        """Soft hidden activations for training: sigma(beta*(h - theta))"""
        h = (np.sqrt(self.nh) / self.nv) * (self.xi.T @ v)
        return 1.0 / (1.0 + np.exp(-self.beta * (h - self.theta)))

    def _reconstruct(self, s: np.ndarray) -> np.ndarray:
        """Reconstruct visible from hidden: v = (1/sqrt(Nh)) * xi * s, then L2 normalize"""
        v_out = (1.0 / np.sqrt(self.nh)) * (self.xi @ s)
        norm = np.linalg.norm(v_out)
        if norm > 1e-8:
            v_out /= norm
        return v_out

    def recall(self, v: np.ndarray, max_iter: int = 10, eps: float = 1e-6) -> tuple:
        """Pattern completion: iterate update rules to convergence.

        Returns (v_recalled, s_hidden).
        """
        v = v.copy().astype(np.float32)
        norm = np.linalg.norm(v)
        if norm > 1e-8:
            v /= norm

        s = self.get_hidden_activations(v)
        for _ in range(max_iter):
            s = self.get_hidden_activations(v)
            v_new = self._reconstruct(s)
            if np.linalg.norm(v_new - v) < eps:
                return v_new, s
            v = v_new

        return v, s

    def learn(self, patterns: np.ndarray, epochs: int = 5) -> float:
        """Train weights to store patterns via gradient descent.

        Uses sigmoid approximation for differentiable Heaviside.
        Returns final mean reconstruction error.
        """
        n = patterns.shape[0]
        lr_eff = self.lr / (1.0 + self.n_patterns_trained / 1000.0)  # Decay

        last_loss = float('inf')
        for epoch in range(epochs):
            total_loss = 0.0
            for i in range(n):
                v = patterns[i]

                # Forward (soft activations for gradient)
                s_soft = self._sigmoid_hidden(v)
                v_recon = (1.0 / np.sqrt(self.nh)) * (self.xi @ s_soft)
                norm = np.linalg.norm(v_recon)
                if norm > 1e-8:
                    v_recon_normed = v_recon / norm
                else:
                    v_recon_normed = v_recon

                # Loss: ||v - v_recon_normed||^2
                error = v - v_recon_normed
                loss = float(np.sum(error ** 2))
                total_loss += loss

                # Gradient through reconstruction
                # d_loss/d_v_recon_normed = -2 * error
                # Gradient of L2-normalize: (I - v_hat v_hat^T) / ||v_recon||
                d_loss_d_vhat = -2.0 * error
                if norm > 1e-8:
                    d_loss_d_vrecon = (d_loss_d_vhat - np.dot(d_loss_d_vhat, v_recon_normed) * v_recon_normed) / norm
                else:
                    d_loss_d_vrecon = d_loss_d_vhat

                # v_recon = (1/sqrt(Nh)) * xi @ s_soft
                # d_loss/d_xi (direct, treating s_soft as const) = (1/sqrt(Nh)) * d_loss_d_vrecon outer s_soft
                grad_direct = (1.0 / np.sqrt(self.nh)) * np.outer(d_loss_d_vrecon, s_soft)

                # Gradient through s_soft = sigma(beta*(xi^T v * sqrt(Nh)/Nv - theta))
                # d_s_soft/d_xi = diag(ds_dh) * (sqrt(Nh)/Nv) * v^T  => shape (Nh, Nv)
                # d_loss/d_s_soft = (1/sqrt(Nh)) * xi^T @ d_loss_d_vrecon
                d_loss_d_ssoft = (1.0 / np.sqrt(self.nh)) * (self.xi.T @ d_loss_d_vrecon)
                ds_dh = self.beta * s_soft * (1.0 - s_soft)  # sigmoid derivative, shape (Nh,)
                # d_loss/d_xi via s_soft path: outer(v, ds_dh * d_loss_d_ssoft) * sqrt(Nh)/Nv
                grad_sigmoid = (np.sqrt(self.nh) / self.nv) * np.outer(v, ds_dh * d_loss_d_ssoft)

                # Update
                self.xi -= lr_eff * (grad_direct + grad_sigmoid)

            last_loss = total_loss / n

        self.n_patterns_trained += n
        return last_loss

    def get_state(self) -> dict:
        """Serialize network state."""
        return {
            'xi': self.xi.copy(),
            'nv': self.nv,
            'nh': self.nh,
            'theta': self.theta,
            'beta': self.beta,
            'lr': self.lr,
            'n_patterns_trained': self.n_patterns_trained,
        }

    @classmethod
    def from_state(cls, state: dict) -> 'DenseAssociativeMemory':
        """Reconstruct from serialized state."""
        net = cls(
            nv=state['nv'], nh=state['nh'],
            theta=state['theta'], beta=state['beta'], lr=state['lr'],
        )
        net.xi = state['xi'].copy()
        net.n_patterns_trained = state['n_patterns_trained']
        return net
