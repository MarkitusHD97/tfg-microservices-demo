#!/bin/bash

# Assegurar que qualsevol caiguda del script aturi la càrrega
trap stop_load EXIT

function log() {
    echo -e "\n[$(date +'%H:%M:%S')] $1"
}

function set_load() {
    local users=$1
    local rate=$2
    log "Ajustant càrrega d'usuaris: Usuaris objectiu: $users (Spawn rate: $rate/s)"
    microk8s kubectl exec deploy/loadgenerator -c main -- wget -q -O- --post-data "user_count=${users}&spawn_rate=${rate}" http://localhost:8089/swarm > /dev/null
    
    if [ $? -ne 0 ]; then
         echo "Error establint contacte amb la API de Locust a loadgenerator."
    fi
}

function stop_load() {
    log "Aturant generació de càrrega completament..."
    microk8s kubectl exec deploy/loadgenerator -c main -- wget -q -O- http://localhost:8089/stop > /dev/null 2>&1
}

function set_scenario_env() {
    local env_val=$1
    log "Configurant SCENARIO_TYPE=$env_val a loadgenerator i esperant rollout..."
    microk8s kubectl set env deployment/loadgenerator SCENARIO_TYPE=$env_val
    microk8s kubectl rollout status deployment/loadgenerator --timeout=120s
    sleep 5
}

function run_scenario_1() {
    log "======================================================="
    log " ESCENARI 1: BASELINE"
    log "======================================================="
    
    log "Warm-up (60 s)..."
    set_load 10 1
    sleep 60
    
    log "Estabilització (5 min)..."
    sleep 300
    
    log "Cooldown (60 s)..."
    stop_load
    sleep 60
    
    log "Escenari 1 finalitzat!"
}

function run_scenario_2() {
    log "======================================================="
    log " ESCENARI 2: ESCALAT PROGRESSIU"
    log "======================================================="
    
    local rate=2
    local hold_time=300 # Segons que manté la càrrega abans del següent escalat

    log "Warm-up (60 s)..."
    set_load 10 1
    sleep 60
    
    log "Pujant a 100 usuaris..."
    set_load 100 $rate
    sleep 45 # temps de pujada
    log "Estabilització (5 min)..."
    sleep $hold_time
    
    log "Pujant a 200 usuaris..."
    set_load 200 $rate
    sleep 50
    log "Estabilització (5 min)..."
    sleep $hold_time
    
    log "Pujant a 300 usuaris..."
    set_load 300 $rate
    sleep 50
    log "Estabilització (5 min)..."
    sleep $hold_time

    log "Pujant a 400 usuaris..."
    set_load 400 $rate
    sleep 50
    log "Estabilització (5 min)..."
    sleep $hold_time

    log "Cooldown (60 s)..."
    stop_load
    sleep 60
    
    log "Escenari 2 finalitzat!"
}

function run_scenario_3() {
    log "======================================================="
    log " ESCENARI 3: REBAIXES"
    log "======================================================="
    
    # Canviar variable d'entorn per a escenari de rebaixes
    set_scenario_env "sales"

    log "Warm-up (60 s)..."
    set_load 10 1
    sleep 60

    log "Pujant a a 500 usuaris..."
    set_load 500 10
    sleep 49
    
    log "Estabilització (5 min)..."
    sleep 300
    
    log "Cooldown (60 s)..."
    stop_load
    sleep 60
    
    # Restaurar valor per defecte
    set_scenario_env "normal"
    
    log "Escenari 3 finalitzat!"
}

function run_scenario_4() {
    log "======================================================="
    log " ESCENARI 4: PIC"
    log "======================================================="
    
    local rate=20

    # Canviar variable d'entorn per a escenari d'oferta limitada
    set_scenario_env "browse"

    log "Warm-up (60 s)..."
    set_load 10 1
    sleep 60
    
    log "Pujant ràpidament a 700 usuaris..."
    set_load 700 $rate
    sleep 35
    
    log "Estabilització (60 s)..."
    sleep 60

    log "Baixant ràpidament a 10 usuaris..."
    set_load 10 $rate
    sleep 35

    log "Estabilització (60 s)..."
    sleep 60
    
    log "Cooldown (60 s)..."
    stop_load
    sleep 60

    # Restaurar valor per defecte
    set_scenario_env "normal"
    
    log "Escenari 4 finalitzat!"
}

function run_scenario_5() {
    log "======================================================="
    log " ESCENARI 5: ALTA VARIABILITAT"
    log "======================================================="

    log "Warm-up (60 s)..."
    set_load 10 1
    sleep 60
    
    log "Pujada inicial a 200 usuaris..."
    set_load 200 10
    sleep 19
    
    log "Baixada a 50 usuaris..."
    set_load 50 5
    sleep 30
    
    log "Pujada a 300 usuaris..."
    set_load 300 5
    sleep 50
    
    log "Baixada a 100 usuaris..."
    set_load 100 10
    sleep 20    
    
    log "Cooldown (60 s)..."
    stop_load
    sleep 60
    
    log "Escenari 5 finalitzat!"
}

# Inici del script

log "Comprovant connexió amb l'API de Locust..."
microk8s kubectl exec deploy/loadgenerator -c main -- wget -q -O- http://localhost:8089/stats/requests > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: No s'ha pogut establir connexió amb Locust."
    exit 1
fi

# Assegurar que no hi ha càrrega prèvia en execució
stop_load
sleep 5

# Permetre executar un escenari concret (argument) o tots (per defecte)
SCENARIO=${1:-all}

if [ "$SCENARIO" == "1" ] || [ "$SCENARIO" == "all" ]; then
    run_scenario_1
fi

if [ "$SCENARIO" == "2" ] || [ "$SCENARIO" == "all" ]; then
    run_scenario_2
fi

if [ "$SCENARIO" == "3" ] || [ "$SCENARIO" == "all" ]; then
    run_scenario_3
fi

if [ "$SCENARIO" == "4" ] || [ "$SCENARIO" == "all" ]; then
    run_scenario_4
fi

if [ "$SCENARIO" == "5" ] || [ "$SCENARIO" == "all" ]; then
    run_scenario_5
fi

log "EXECUCIÓ FINALITZADA!"
