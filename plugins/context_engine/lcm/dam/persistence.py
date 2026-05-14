"""Save and load DAM network state to disk."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def save_state(retriever, path: Path) -> bool:
    """Save retriever state to a .npz file."""
    try:
        import numpy as np
        net = getattr(retriever, 'net', None) or getattr(retriever, 'network')
        state = {
            'xi': net.xi,
            'nv': np.array(net.nv),
            'nh': np.array(net.nh),
            'theta': np.array(net.theta),
            'beta': np.array(net.beta),
            'lr': np.array(net.lr),
            'n_patterns_trained': np.array(net.n_patterns_trained),
            'last_indexed_id': np.array(retriever._last_indexed_id),
        }
        if retriever._pattern_cache:
            cache_ids = np.array(sorted(retriever._pattern_cache.keys()), dtype=np.int64)
            cache_vectors = np.stack([retriever._pattern_cache[i] for i in cache_ids])
            state['cache_ids'] = cache_ids
            state['cache_vectors'] = cache_vectors

        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(str(path), **state)
        return True
    except Exception as e:
        logger.warning("Failed to save DAM state: %s", e)
        return False


def load_state(path: Path) -> Optional[dict]:
    """Load retriever state from a .npz file."""
    try:
        import numpy as np
        if not path.exists():
            return None
        data = np.load(str(path), allow_pickle=False)
        state = {
            'xi': data['xi'],
            'nv': int(data['nv']),
            'nh': int(data['nh']),
            'theta': float(data['theta']),
            'beta': float(data['beta']),
            'lr': float(data['lr']),
            'n_patterns_trained': int(data['n_patterns_trained']),
            'last_indexed_id': int(data['last_indexed_id']),
            'cache_ids': data.get('cache_ids'),
            'cache_vectors': data.get('cache_vectors'),
        }
        return state
    except Exception as e:
        logger.warning("Failed to load DAM state: %s", e)
        return None
