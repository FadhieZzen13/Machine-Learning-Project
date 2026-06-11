"""
Neural-network meta-classifier.

Architecture (as suggested by the assignment):
    Input features -> Dense(ReLU) -> Dense(ReLU) -> Softmax over global classes

Implemented in PyTorch (PyTorch is already a dependency via ultralytics/YOLO).
Training data is a table of (feature_vector, global_class_label) rows that you
produce by running the YOLO models over a labelled validation set and recording
their detections + the ground-truth final class. See docs/project_plan.md
"Meta-classifier data" for how to generate it.

This file is a SKELETON: the network and train loop are complete and runnable
once torch is installed and a features.npz dataset exists, but no training has
been performed yet.
"""
from __future__ import annotations

import argparse
import os

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    _TORCH = True
except ImportError:  # allow importing this module without torch present
    _TORCH = False


if _TORCH:

    class MetaClassifier(nn.Module):
        def __init__(self, in_dim: int, num_classes: int, hidden: int = 128):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_dim, hidden),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden, hidden // 2),
                nn.ReLU(),
                nn.Linear(hidden // 2, num_classes),
            )

        def forward(self, x):
            return self.net(x)  # raw logits; use softmax/argmax at inference

    def train(features_npz: str, out_path: str, epochs: int = 50,
              batch_size: int = 64, lr: float = 1e-3):
        """Train the meta-classifier from a .npz with arrays X (float32) and y (int)."""
        data = np.load(features_npz)
        X, y = data["X"].astype(np.float32), data["y"].astype(np.int64)
        n_classes = int(y.max()) + 1

        # simple 80/20 split
        idx = np.random.permutation(len(X))
        split = int(0.8 * len(X))
        tr, va = idx[:split], idx[split:]

        def loader(ii, shuffle):
            ds = TensorDataset(torch.from_numpy(X[ii]), torch.from_numpy(y[ii]))
            return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

        model = MetaClassifier(X.shape[1], n_classes)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()

        for ep in range(1, epochs + 1):
            model.train()
            for xb, yb in loader(tr, True):
                opt.zero_grad()
                loss = loss_fn(model(xb), yb)
                loss.backward()
                opt.step()
            # validation accuracy
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for xb, yb in loader(va, False):
                    pred = model(xb).argmax(1)
                    correct += (pred == yb).sum().item()
                    total += len(yb)
            if ep % 10 == 0 or ep == epochs:
                print(f"epoch {ep:>3}  val_acc={correct / max(total,1):.3f}")

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        torch.save({"state_dict": model.state_dict(),
                    "in_dim": X.shape[1], "num_classes": n_classes}, out_path)
        print(f"saved -> {out_path}")

    def load_model(path: str) -> "MetaClassifier":
        ckpt = torch.load(path, map_location="cpu")
        m = MetaClassifier(ckpt["in_dim"], ckpt["num_classes"])
        m.load_state_dict(ckpt["state_dict"])
        m.eval()
        return m


if __name__ == "__main__":
    if not _TORCH:
        raise SystemExit("PyTorch not installed. `pip install torch` to train.")
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="../../data/meta_classifier/features.npz")
    ap.add_argument("--out", default="../../models/meta_classifier.pt")
    ap.add_argument("--epochs", type=int, default=50)
    args = ap.parse_args()
    train(args.features, args.out, epochs=args.epochs)
