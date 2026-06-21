# Treball de Fi de Grau - Disseny i implementació d’una arquitectura de microserveis amb mecanismes de monitorització i escalat automàtic

**Autor:** Marc Esteve Rodríguez

## Resum
Aquest Treball de Final de Grau, realitzat en el Grau en Enginyeria Informàtica de la Facultat d'Informàtica de Barcelona (FIB), estudia el comportament de diferents estratègies d'escalat automàtic desplegades sobre Kubernetes. L'objectiu del treball és analitzar les limitacions de l'escalat tradicional basat en ús de CPU i comparar-lo amb alternatives basades en altres mètriques, com la latència, les peticions per segon o l'ús de memòria. Per dur a terme l'anàlisi s'ha desplegat l'aplicació utilitzada com a cas d'estudi, Online Boutique, en un entorn local, implementant diferents polítiques d'autoescalat i executant diversos escenaris de càrrega reproduïbles. Mitjançant eines de monitorització i observabilitat s'ha analitzat el comportament de cada estratègia en termes de rendiment, estabilitat i capacitat d'adaptació davant canvis en la demanda, amb l'objectiu d'obtenir una millor comprensió dels mecanismes d'autoescalat aplicats a sistemes distribuïts basats en microserveis.

## Abstract
This Final Degree Thesis, carried out within the Degree in Computer Engineering at the Barcelona School of Informatics (FIB), studies the behavior of different autoscaling strategies in microservice architectures deployed on Kubernetes. The objective of this work is to analyze the limitations of traditional CPU-based autoscaling and compare it with alternative approaches based on other metrics, such as latency, requests per second or memory usage. To conduct this study, the Online Boutique application was deployed as a case study in a local environment, implementing different autoscaling policies and executing several reproducible workload scenarios. Using monitoring and observability tools, the behavior of each strategy was analyzed in terms of performance, stability, and adaptability to workload variations, with the aim of achieving a better understanding of autoscaling mechanisms in distributed microservice-based systems.

---

Aquest repositori conté el codi utilitzat i els resultats de la recerca elaborada en aquest TFG.

---

## Organització del repositori

### 1. Manifests d'escalat (`escalat-kustomize/`)
Aquesta carpeta conté tots els manifests `.yaml` que permeten aplicar estrategies d'escalat. Totes les estrategies s'han separat per carpetes seguint l'arquitectura **Kustomize**:

*   `/hpa-cpu/`: Desplegament d'escalat mitjançant Horitzontal Pod Autoscalers basats en ús del processador (CPU).
*   `/hpa-latency/`: Desplegament d'escalat mitjançant `ScaledObjects` de KEDA, fent consultes *PromQL* a la malla d'Istio pel percentil de latència P95.
*   `/hpa-rps/`: Desplegament d'escalat mitjançant `ScaledObjects` de KEDA, fent consultes *PromQL* a la malla d'Istio per obtenir el nombre de RPS.

### 2. Manifests base personalitzats (`kubernetes-manifests-custom/`)
Conté les plantilles base per desplegar l'aplicació en el clúster. A diferència dels originals, aquests fitxers `.yaml` s'han adaptat per utilitzar les imatges de Docker construïdes localment dels serveis que han patit modificacions.

### 3. Utilitats (`scripts/`)
En comptes d'arrencades manuals, s'han dissenyat procediments estrictes automatitzats:
*   `deploy_all.sh`: Script d'inicialització. Construeix localment totes les imatges de Docker dels microserveis des de zero amb els canvis al codi font i els desplega.
*   `update_service.sh`: Compilador individual per a un microservei en concret.
*   `run_experiments.sh`: Script que interacciona amb l'API de Locust per executar els escenaris de carrega i guardar els resultats de forma automatica.
*   `export_metrics.py`: Codi en Python que fa consultes a *Prometheus* per obtenir els resultats dels experiments i guardar-los en arxius CSV.
*   `generate_plots.py`: Codi en Python genera gràfiques i taules a partir dels resultats d'una execucio.

### 4. Resultats i processament (`results/`)
*   Al directori es guarden els resultats .CSV recollits per l'script `export_metrics.py` en una execucio de `run_experiments.sh`.
*   Un cop fets els experiments, gràcies a l'script `generate_plots.py` s'analitza de manera conjunta els resultats d'un experiment. 
*   Aquest procés produeix gràfiques i taules resum amb mètriques rellevants.

### 5. Codi font (`microservices-demo/src/...`)
El codi font original dels serveis de la Online Boutique amb petites modificacions per a fer l'experimentacio mes interessant. Alguns exemples del codi propi alterat:
- Introduccio de latències artificials estocàstiques al codi de `email_server.py` i `paymentservice/server.js`.
- Injecció d'un bule de carrega computacional al codi de `AdService.java`.
- Ampliació de catàleg de productes (`products.json`) mitjançant el script `scripts/scale_catalog.sh`.
- Canvis en la generació de càrrega a `locustfile.py`, canviant els pesos de les operacions en funcio de l'escenari.

### 7. Dades dels experiemtns (`experiments/`)
*   Aquesta carpeta conté les dades processades dels experiments realitzats durant el TFG.
*   Conté totes les taules CSV i gràfiques de les diferents execucions.
*   Està dividida segons cada fase de l'estudi (`control`, `cpu`, `latency`, `rps`).

---

## Insta·lació

Per a poder executar els experiments des de zero en un entorn local (Ubuntu/Debian), es recomana l'ús de **MicroK8s** per la seva facilitat d'instal·lacio mitjançant *add-ons*.

> **Nota de permisos:** Aquesta guia assumeix que l'usuari s'ha afegit al grup d'administració de MicroK8s (tal com s'indica al pas A) per executar-lo de forma nativa. En cas contrari, caldrà escriure `sudo` davant de qualsevol de les comandes i alguns scripts poden no funcionar bé.

### 1. Preparació de l'entorn
Primer de tot cal disposar d'un clúster Kubernetes local. La via més senzilla a Ubuntu/Debian és instal·lar-lo via Snap:

**A.** Instal·lació de MicroK8s i configuració de permisos:
```bash
sudo snap install microk8s --classic
sudo usermod -a -G microk8s $USER
newgrp microk8s
```

**B.** Habilitar els complements bàsics a MicroK8s:
```bash
microk8s enable dns community metrics-server
```

**C.** Habilitar l'stack de Prometheus i posteriorment Istio (Pot trigar una estona)
```bash
microk8s enable observability
microk8s enable istio
```

**D.** Activar la injecció automàtica de la service mesh al namespace per defecte
```bash
microk8s kubectl label namespace default istio-injection=enabled
```

**E.** Vincular les mètriques d'Istio cap a Prometheus mitjançant el PodMonitor
```bash
microk8s kubectl apply -f kubernetes-manifests-custom/istio-pod-monitor.yaml
```

**F.** Modificar l'interval de recollida de mètriques i evaluació de Prometheus a 15 segons
```bash
microk8s kubectl patch prometheus -n observability kube-prom-stack-kube-prome-prometheus --type='merge' -p '{"spec":{"scrapeInterval":"15s", "evaluationInterval":"15s"}}'
```

**G.** Instal·lar KEDA mitjançant Helm
```bash
microk8s helm3 repo add kedacore https://kedacore.github.io/charts
microk8s helm3 repo update
microk8s helm3 install keda kedacore/keda --namespace keda --create-namespace
```

**H.** Grafana (Opcional) 

L'stack instal·lat prèviament ja incorpora Grafana. S'hi pot accedir obrint el port pertinent:
```bash
microk8s kubectl port-forward -n observability service/kube-prom-stack-grafana 3000:80
```
Navegant a `http://localhost:3000` (Usuari: `admin` | Contrasenya: `prom-operator`), a través de la interfície gràfica es pot importar el dashboard de monitorització dissenyat per a l'avaluació d'aquest TFG contingut a `dashboard/dashboard.json`.

Addicionalment, per executar els scripts de l'entorn experimental, es necessita tindre instal·lat **Docker** (per poder construir les imatges abans de la inserció) i **Python 3** amb els següents paquets per processar els resultats:

Instal·lació de Docker
```bash
sudo apt update && sudo apt install -y docker.io
```
Instal·lació de dependències de Python
```bash
sudo apt install -y python3-pip
pip install pandas requests matplotlib
```

### 2. Procés d'execució pas a pas
Un cop el clúster estigui llest, la posada en marxa es divideix en la compilació, l'aplicació d'estratègies i l'experimentació:

**A. Desplegament base:**
Construeix localment les 11 imatges Docker basades en el codi modificat d'aquest repositori i ho desplega el clúster:
```bash
./scripts/deploy_all.sh
```

**B. Comprovació:**
Abans d'aplicar cap escalat, és important corroborar que els 11 microserveis estan en funcionament sota la xarxa d'Istio (han de mostrar `2/2` contenidors llestos):
```bash
microk8s kubectl get pods -n default
```
Per validar que la botiga opera amb normalitat des del navegador, es pot fer obrint el port 8080:
```bash
microk8s kubectl port-forward deployment/frontend 8080:8080
```
*(Es podrà accedir via web navegant cap a `http://localhost:8080`)*

**C. Selecció de l'estratègia d'autoescalat:**
Un cop assegurada llest, apliqueu-li per sobre la capa de *Kustomize* pertinent (per exemple l'HPA per CPU):
```bash
# Opcions disponibles: hpa-cpu | hpa-latency | hpa-rps
microk8s kubectl apply -k escalat-kustomize/hpa-cpu
```

> **Nota:** Per canviar d'una estratègia a una altra sense conflictes, cal revertir primer l'escalat actual amb la clàusula `delete` sobre la mateixa ruta i, abans d'aplicar el nou escalat:
> `microk8s kubectl delete -k escalat-kustomize/hpa-cpu`

**D. Execució d'experiments:**
Executeu el script de proves de càrrega. Aquest s'encarregarà d'establir la connexió amb Prometheus, i cridara a *Locust* per a que orquestri el tràfic, creant automàticament els fitxers de resultats CSV (dins de la carpeta `results/`) al acabar.

L'script accepta 3 arguments opcionals per catalogar i dirigir correctament l'estudi: 
`./scripts/run_experiments.sh [ESCENARI] [NÚMERO_ITERACIÓ] [FASE]`
- **ESCENARI**: `1`, `2`, `3`, `4`, `5` o `all` (per defecte). Especifica quin escenari de càrrega simular. Si se selecciona `all` es fara una execucio completa dels 5 escenaris.
- **NÚMERO_ITERACIÓ**: Número per no sobreescriure resultats si es repeteix un mateix test (per defecte: `1`).
- **FASE**: Etiqueta descriptiva que figurarà al nom de l'arxiu CSV per identificar l'estratègia activa (ex: `control`, `cpu`, `rps`). Per defecte és `control`.

Exemple pràctic per llançar només l'escenari 5, avaluant l'escalat per RPS en la primera repetició del test:
```bash
./scripts/run_experiments.sh 5 1 rps
```

**E. Processament i generació de gràfiques:**
Un cop recollides múltiples iteracions de proves (per exemple de la fase `control`), pots invocar l'script global encarregat de calcular les mitjanes, generar les grafiques i extreure la taula general de mètriques.

Aquest script accepta com a argument el nom de la fase/estratègia que ha estat testada, buscant i agregant tots els resultats coincidents:
```bash
python3 scripts/generate_plots.py [FASE]
```
S'analitzaran automàticament els corresponents CSV i es dipositaran els resultats de les grafiques `.png` així com l'informe `resum_kpis_fase_XXX.csv` dins la mateixa carpeta  `results/`.
