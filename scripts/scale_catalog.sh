#!/bin/bash

# Assegurar que hi ha un argument (nombre total de productes)
if [ -z "$1" ]; then
  echo "Ús: $0 <nombre_total_productes>"
  echo "Exemple per tenir 1000 productes: $0 1000"
  exit 1
fi

TOTAL=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)"
PRODUCTS_FILE="$SCRIPT_DIR/microservices-demo/src/productcatalogservice/products.json"
UPDATE_SCRIPT="$SCRIPT_DIR/scripts/update_service.sh"

if [ ! -f "$PRODUCTS_FILE" ]; then
  echo "Error: No es troba l'arxiu $PRODUCTS_FILE"
  exit 1
fi

echo "=== Modificant products.json fins a tenir $TOTAL productes ==="
python3 - <<EOF
import json
import uuid
import random

total = int("$TOTAL")
file_path = "$PRODUCTS_FILE"

with open(file_path, 'r') as f:
    data = json.load(f)

products = data.get("products", [])
current = len(products)

if total > current:
    base_product = products[0]
    for i in range(total - current):
        new_prod = base_product.copy()
        new_prod["id"] = "GEN-" + str(uuid.uuid4())[:8] # ID curt generat
        new_prod["name"] = f"Producte generat {current + i + 1}"
        new_prod["description"] = f"Aquest és un producte autogenerat per a experimentació. Número: {current + i + 1}."
    
        new_prod["priceUsd"]["units"] = random.randint(1, 500)
        new_prod["priceUsd"]["nanos"] = 990000000
        
        products.append(new_prod)
    
    data["products"] = products
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"S'han creat {total - current} productes nous de forma automàtica. Total al catàleg: {len(products)}.")
elif total < current:
    # Retallar
    data["products"] = products[:total]
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"S'han esborrat {current - total} productes. Total al catàleg: {len(data['products'])}.")
else:
    print(f"Ja hi ha exactament {current} productes.")
EOF

echo "=== Actualitzant productcatalogservice ==="
if [ -f "$UPDATE_SCRIPT" ]; then
    bash "$UPDATE_SCRIPT" productcatalogservice
else
    echo "Error: No s'ha trobat l'update_script a $UPDATE_SCRIPT"
fi

echo "=== Tenda actualitzada amb el nou volum de prooductes! ==="
