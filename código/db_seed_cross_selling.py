import pymongo
import random
from faker import Faker
import datetime

# Configuración de MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["cross_selling3"]

# Crear instancias de las colecciones
customers_collection = db["customers"]
category_collection = db["category"]
products_collection = db["products"]
interactions_collection = db["interactions"]

# Limpiar la base de datos existente
customers_collection.delete_many({})
category_collection.delete_many({})
products_collection.delete_many({})
interactions_collection.delete_many({})

# Instancia de Faker
fake = Faker()

# Generar categorías
def generate_categories(n_categories=10):
    categories = []
    for i in range(n_categories):
        category = {
            "_id": str(i + 1),
            "active": random.choice([0, 1]),
            "name": fake.word(),
            "parent_category": random.choice([None] + [str(j) for j in range(1, i)]),
            "root_category": 1 if i == 0 else 0,
            "description": fake.text(),
            "meta_title": fake.sentence(),
            "meta_keywords": fake.words(5),
            "meta_description": fake.text(),
            "url_rewritten": fake.slug(),
            "image_url": fake.image_url(),
        }
        categories.append(category)
    category_collection.insert_many(categories)

# Generar clientes
def generate_customers(n_customers=1000):
    customers = []
    for i in range(n_customers):
        customer = {
            "_id": str(i + 1),
            "active": random.choice([0, 1]),
            "titles_id": random.choice([1, 2, 0]),
            "email": fake.email(),
            "password": fake.password(),
            "birthday": fake.date_of_birth().strftime("%Y-%m-%d"),
            "last_name": fake.last_name(),
            "first_name": fake.first_name(),
            "newsletter": random.choice([0, 1]),
            "opt_in": random.choice([0, 1]),
            "registration_date": fake.date_this_decade().strftime("%Y-%m-%d"),
            "groups": ",".join([str(random.randint(1, 5)) for _ in range(random.randint(1, 3))]),
            "default_group_id": str(random.randint(1, 5)),
        }
        customers.append(customer)
    customers_collection.insert_many(customers)

# Generar productos
def generate_products(n_products=500):
    products = []
    for i in range(n_products):
        product = {
            "_id": str(i + 1),
            "active": random.choice([0, 1]),
            "name": fake.catch_phrase(),
            "categories": ",".join([str(random.randint(1, 10)) for _ in range(random.randint(1, 3))]),
            "price_tax_excluded": round(random.uniform(5.0, 500.0), 2),
            "tax_rules_id": str(random.randint(1, 5)),
            "wholesale_price": round(random.uniform(1.0, 100.0), 2),
            "on_sale": random.choice([0, 1]),
            "discount_amount": round(random.uniform(0.0, 50.0), 2),
            "discount_percent": round(random.uniform(0.0, 100.0), 2),
            "discount_from": fake.date_this_year().strftime("%Y-%m-%d"),
            "discount_to": fake.date_this_year().strftime("%Y-%m-%d"),
            "reference": fake.uuid4(),
            "manufacturer": fake.company(),
            "quantity": random.randint(0, 1000),
            "minimal_quantity": random.randint(1, 5),
            "visibility": random.choice(["visible", "hidden"]),
            "description": fake.text(),
            "tags": fake.words(5),
            "meta_title": fake.sentence(),
            "meta_description": fake.text(),
            "image_urls": [fake.image_url() for _ in range(random.randint(1, 3))],
        }
        products.append(product)
    products_collection.insert_many(products)

# Generar interacciones
def generate_interactions(n_interactions=100000):
    customer_ids = [customer["_id"] for customer in customers_collection.find()]
    product_ids = [product["_id"] for product in products_collection.find()]
    interactions = []

    for _ in range(n_interactions):
        interaction = {
            "customer_id": int(random.choice(customer_ids)),
            "product_id": int(random.choice(product_ids)),
            "interaction": round(random.uniform(0.0, 5.0), 2),  # Puede ser int o float
            "timestamp": fake.date_time_this_year(),
        }
        interactions.append(interaction)
    
    # Inserción en lotes para mayor rendimiento
    batch_size = 1000
    for i in range(0, len(interactions), batch_size):
        interactions_collection.insert_many(interactions[i:i + batch_size])

# Llamadas para generar los datos
print("Generando categorías...")
generate_categories(n_categories=10)

print("Generando clientes...")
generate_customers(n_customers=1000)

print("Generando productos...")
generate_products(n_products=500)

print("Generando interacciones...")
generate_interactions(n_interactions=100000)

print("¡Base de datos generada exitosamente!")
