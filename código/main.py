from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["cross_selling3"]

# Inicializar FastAPI
app = FastAPI()

# Cargar datos desde MongoDB
def load_data():
    interactions = pd.DataFrame(list(db.interactions.find()))
    
    if interactions.empty:
        raise RuntimeError("No se encontraron interacciones en la base de datos.")
    return interactions

# Crear matriz de interacción
def create_interaction_matrix(interactions):
    matrix = interactions.pivot_table(
        index="customer_id", columns="product_id", values="interaction", fill_value=0
    )
    sparse_matrix = csr_matrix(matrix)
    return sparse_matrix, matrix

# Entrenar modelo KNN
def train_knn(sparse_matrix):
    knn_model = NearestNeighbors(metric="cosine", algorithm="brute")
    knn_model.fit(sparse_matrix)
    return knn_model

# Cargar modelo KNN (entrenar si es necesario)
try:
    interactions = load_data()
    sparse_matrix, interaction_matrix = create_interaction_matrix(interactions)
    knn_model = train_knn(sparse_matrix)
    print("Modelo KNN entrenado con éxito.")
except Exception as e:
    print(f"Error durante la carga o entrenamiento del modelo: {e}")

# Endpoints
@app.post("/register_customer")
async def register_customer(first_name: str, last_name: str, email: str):
    customer = {"first_name": first_name, "last_name": last_name, "email": email}
    result = db.customers.insert_one(customer)
    return {"message": "Cliente registrado correctamente", "customer_id": str(result.inserted_id)}

@app.post("/register_category")
async def register_category(name: str, parent_category: str = None):
    category = {"name": name, "parent_category": parent_category}
    result = db.category.insert_one(category)
    return {"message": "Categoría registrada correctamente", "category_id": str(result.inserted_id)}

@app.post("/register_product")
async def register_product(name: str, categories: list, price: float):
    product = {"name": name, "categories": categories, "price": price}
    result = db.products.insert_one(product)
    return {"message": "Producto registrado correctamente", "product_id": str(result.inserted_id)}

@app.post("/register_interaction")
async def register_interaction(customer_id: str, product_id: str, interaction: int):
    interaction_data = {"customer_id": customer_id, "product_id": product_id, "interaction": interaction}
    result = db.interactions.insert_one(interaction_data)
    return {"message": "Interacción registrada correctamente", "interaction_id": str(result.inserted_id)}

@app.get("/recommend/{customer_id}")
async def recommend(customer_id: str, top_n: int = Query(5, ge=1, le=20, description="Número de recomendaciones")):
    # Verificar si el cliente existe en la base de datos
    if customer_id not in interaction_matrix.index:
        raise HTTPException(status_code=404, detail=f"Cliente con ID {customer_id} no encontrado")

    # Obtener las recomendaciones
    customer_index = interaction_matrix.index.get_loc(customer_id)
    distances, indices = knn_model.kneighbors(interaction_matrix.iloc[customer_index, :].values.reshape(1, -1), n_neighbors=top_n + 1)

    # Excluir el propio cliente de los resultados
    similar_customers = indices.flatten()[1:]
    recommended_products = interaction_matrix.iloc[similar_customers].sum(axis=0).sort_values(ascending=False)
    recommended_products = recommended_products[interaction_matrix.loc[customer_id] == 0].head(top_n)

    return {"customer_id": customer_id, "recommendations": recommended_products.index.tolist()}
