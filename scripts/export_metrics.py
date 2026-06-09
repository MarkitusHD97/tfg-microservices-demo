import sys
import os
import requests
import pandas as pd

# Configuració base
PROMETHEUS_URL = "http://localhost:9090/api/v1/query_range"
STEP = "15s"  # Interval de mostreig

# Llistat de serveis a monitoritzar
SERVICES = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis-cart", "shippingservice"]

# Consultes PromQL
QUERIES = {
    "RPS": 'sum(rate(istio_requests_total{{reporter="destination", destination_workload="{service}", namespace="default"}}[1m]))',
    "Errors_5xx": 'sum(rate(istio_requests_total{{reporter="destination", destination_workload="{service}", namespace="default", response_code=~"5.."}}[1m])) or vector(0)',
    "Latency_P50": 'histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{{reporter="destination", destination_workload="{service}", namespace="default"}}[1m])) by (le))',
    "Latency_P95": 'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{{reporter="destination", destination_workload="{service}", namespace="default"}}[1m])) by (le))',
    "Latency_P99": 'histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{{reporter="destination", destination_workload="{service}", namespace="default"}}[1m])) by (le))',
    "Replics": 'kube_deployment_status_replicas_available{{deployment="{service}", namespace="default"}}',
    "CPU_Usage": 'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{{namespace="default", pod=~"{service}-.*"}})',
    "RAM_Usage": 'sum(container_memory_working_set_bytes{{namespace="default", pod=~"{service}-.*", container!=""}})'
}

def fetch_metric(query, start, end):
    params = {"query": query, "start": start, "end": end, "step": STEP}
    try:
        response = requests.get(PROMETHEUS_URL, params=params).json()
        results = response['data']['result']
        if not results:
            return pd.DataFrame()
        
        # Extreure els punts temporals [timestamp, valor]
        values = results[0]['values']
        df = pd.DataFrame(values, columns=['Timestamp', 'Value'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
        df['Value'] = pd.to_numeric(df['Value'])
        return df
    except Exception as e:
        print(f"Error consultant Prometheus: {e}")
        return pd.DataFrame()

def main():
    if len(sys.argv) < 4:
        print("Ús: python export_metrics.py [Nom_experiment] [Timestamp_inici] [Timestamp_final]")
        sys.exit(1)
        
    experiment_name = sys.argv[1]
    start_time = sys.argv[2]
    end_time = sys.argv[3]
    
    main_df = pd.DataFrame()
    
    print(f"Iniciant extracció de dades per a: {experiment_name}...")
    
    for service in SERVICES:
        for metric_name, query_template in QUERIES.items():
            query = query_template.format(service=service)
            df = fetch_metric(query, start_time, end_time)
            
            if not df.empty:
                column_title = f"{service}_{metric_name}"
                df = df.rename(columns={'Value': column_title})
                
                if main_df.empty:
                    main_df = df
                else:
                    main_df = pd.merge(main_df, df, on='Timestamp', how='outer')
                    
    if not main_df.empty:
        # Ordenar per temps i guardar
        main_df = main_df.sort_values(by='Timestamp')
        filename = f"results_{experiment_name}.csv"
        main_df.to_csv(filename, index=False)
        print(f"Dades guardades correctament a: {filename}")
    else:
        print("No s'han pogut recuperar dades per a aquest rang de temps.")

if __name__ == "__main__":
    main()