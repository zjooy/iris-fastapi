"""Treina o classificador Iris e salva os artefatos usados pela API.

Equivalente em script ao `train_model.ipynb` (mantido para exploração
interativa), mas reprodutível via linha de comando / CI:

    python scripts/train_model.py
"""

import pickle
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "app" / "ml" / "artifacts"


def main() -> None:
    iris = load_iris()
    X, y = iris.data, iris.target

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)

    acuracia = accuracy_score(y_test, modelo.predict(X_test))
    print(f"Acurácia no conjunto de teste: {acuracia:.2%}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(ARTIFACTS_DIR / "modelo_iris.pkl", "wb") as f:
        pickle.dump(modelo, f)

    with open(ARTIFACTS_DIR / "classes_iris.pkl", "wb") as f:
        pickle.dump(list(iris.target_names), f)

    print(f"Artefatos salvos em {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
