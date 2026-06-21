#!/bin/bash

echo "=== Iniciant desplegament complet de l'entorn de l'experiment ==="

SERVICES="adservice emailservice frontend paymentservice productcatalogservice recommendationservice loadgenerator"

for service in $SERVICES; do
    echo "-> Generat imatge de: $service"
    ./scripts/update_service.sh "$service"
    if [ $? -ne 0 ]; then
        echo "Error creant el servei $service. S'ha abortat l'script."
        exit 1
    fi
done

echo "=== Aplicant manifests de Kubernetes ==="
microk8s kubectl apply -f ./kubernetes-manifests-custom/

echo "=== Desplegament base llest! ==="
