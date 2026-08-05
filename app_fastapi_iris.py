from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import numpy as np

class IrisRequest(BaseModel):
    """"
    MODELO DE ENTRADA - Define os dados que o cliente deve enviar para /predict
    """
    sepal_length: float = Field(..., example=5.1, description="Comprimento da sépala em cm")
    sepal_width: float = Field(..., example=3.5, description="Largura da sépala em cm")
    petal_length: float = Field(..., example=1.4, description="Comprimento do pétala em cm")
    petal_width: float = Field(..., example=0.2, description="Largura do pétala em cm")


class IrisPrediction(BaseModel):
    """
    MODELO DE PREDIÇÃO - Define os dados que o cliente receberá de /predict
    """
    classe : str = Field(..., example="Iris-setosa", description="Nome da espécie prevista pelo modelo")
    classe_idx: int = Field(..., example=0, description="Índice numerico da espécie prevista pelo modelo")

class IrisProbability(BaseModel):
    """
    MODELO DE PROBABILIDADE - Probabilidade por classe
    """
    setosa: float = Field(..., example=0.9, description="Probabilidade da espécie Iris-setosa")
    versicolor: float = Field(..., example=0.05, description="Probabilidade da espécie Iris-versicolor")
    virginica: float = Field(..., example=0.05, description="Probabilidade da espécie Iris-virginica")

class IrisResponse(BaseModel):
    """
    MODELO DE RESPOSTA - Define os dados que o cliente receberá de /predict
    """
    sucesso: bool = Field(..., example=True, description="Indica se a predição foi realizada com sucesso")
    prediction: IrisPrediction = Field(..., description="Predição do modelo")
    probability: IrisProbability = Field(..., description="Probabilidade por classe")   
    entrada_recebida: IrisRequest = Field(..., description="Dados de entrada recebidos para a predição")

try:
    with open("modelo_iris.pkl", "rb") as f:
        modelo = pickle.load(f)
    with open("classes_iris.pkl", "rb") as f:
        classes = pickle.load(f)
    MODELO_CARREGADO = True
except FileNotFoundError:
    print("Arquivos Do Modelo não encontrado")
    modelo = None
    classes = None
    MODELO_CARREGADO = False

app = FastAPI(
    title="API de Classificação de Espécies de Flores Iris", 
    description="Esta API realiza classificações de espécies de Iris com base em medidas de sépalas e pétalas.", 
    version="1.0.0")

@app.get("/")
def home():
    """
        Rota raiz da API - Retorna uma mensagem de boas-vindas e informações sobre a API
        URL para verificar se a API esta no ar e requisicoes disponiveis
    
        test curl http://127.0.0.1:8000/
    """ 
    return {
        "nome": "API de Classificação de Espécies de Flores Iris",
        "versao": "1.0.0",
        "descricao": "Esta API realiza classificações de espécies de Iris com base em medidas de sépalas e pétalas.",
        "endpoints": {
            "GET /": "Rota raiz da API - Retorna uma mensagem de boas-vindas e informações sobre a API",
            "GET /health": "Rota de saúde da API - Retorna o status da API e se o modelo está carregado",
            "GET /docs": "Rota de documentação da API - Retorna a documentação interativa da API",
            "POST /predict": "Rota de predição - Recebe medidas de sépalas e pétalas e retorna a espécie prevista, probabilidade por classe e os dados de entrada recebidos"
        },
        "modelo_carregado": MODELO_CARREGADO
    }


@app.get("/health")
def health():
    """
        Rota de saúde da API - Retorna o status da API e se o modelo está carregado
        URL para verificar se a API esta no ar e requisicoes disponiveis
    """
    return {
        "status": "healthy" if MODELO_CARREGADO else "unhealthy",
        "modelo_carregado": MODELO_CARREGADO
    }

@app.post("/predict", response_model=IrisResponse)
def predict(payload: IrisRequest) -> IrisResponse:
    """
        Rota de predição - Recebe medidas de sépalas e pétalas e retorna a espécie prevista, probabilidade por classe e os dados de entrada recebidos
        URL para realizar predições
    """
    if not MODELO_CARREGADO:
        raise HTTPException(
            status_code=503, 
            detail="Modelo não carregado. Verifique se os arquivos .pkl estão disponiveis.")

    features = np.array([[
        payload.sepal_length, 
        payload.sepal_width, 
        payload.petal_length, 
        payload.petal_width]])

    prediction_idx = modelo.predict(features)[0]
    probabilities = modelo.predict_proba(features)[0]

    return IrisResponse(
        sucesso=True,
        prediction=IrisPrediction(
            classe=classes[prediction_idx],
            classe_idx=int(prediction_idx)
        ),
        probability=IrisProbability(
            setosa=round(float(probabilities[0]), 4),
            versicolor=round(float(probabilities[1]), 4),
            virginica=round(float(probabilities[2]), 4)
        ),
        entrada_recebida=payload
    )

    