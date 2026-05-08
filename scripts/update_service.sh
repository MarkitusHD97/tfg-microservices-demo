#!/bin/bash

# Assegurar que hi ha un argument (nom del servei)
if [ -z "$1" ]; then
  echo "Ús: $0 <nom_del_servei>"
  echo "Exemple: $0 emailservice"
  exit 1
fi

SERVICE=$1
# Assegurar que estem buscant a la carpeta src correcta
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)"
DIR="$SCRIPT_DIR/microservices-demo/src/$SERVICE"

if [ ! -d "$DIR" ]; then
  echo "Error: El directori del servei '$DIR' no existeix."
  exit 1
fi

echo "=== Iniciant actualització de $SERVICE ==="
cd "$DIR" || exit 1

echo "=== Construint la imatge Docker ==="
sudo docker build -t "${SERVICE}:latest" .
if [ $? -ne 0 ]; then
    echo "Error construint la imatge."
    exit 1
fi

echo "=== Exportant de Docker i important a MicroK8s (containerd) ==="
sudo docker save "${SERVICE}:latest" | microk8s ctr images import -
if [ $? -ne 0 ]; then
    echo "Error al importar la imatge."
    exit 1
fi

echo "=== Reiniciant el deployment a Kubernetes ==="
microk8s kubectl rollout restart deployment "${SERVICE}"

echo "=== $SERVICE actualitzat correctament! ==="
