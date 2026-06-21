import os
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt

def load_and_average_runs(fase, scenario_num):
    pattern = f"results/results_{fase}_escenari{scenario_num}_run*.csv"
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No s'han trobat fitxers CSV per a la fase '{fase}', escenari {scenario_num}")
        return None
    
    print(f"Processant {len(files)} repeticions per a l'escenari {scenario_num} de la fase '{fase}'...")
    
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp').reset_index(drop=True)
        dfs.append(df)
        
    min_rows = min(len(d) for d in dfs)
    dfs = [d.iloc[:min_rows] for d in dfs]
    
    avg_df = pd.DataFrame()
    avg_df['Timestamp'] = dfs[0]['Timestamp']
    
    start_time = avg_df['Timestamp'].iloc[0]
    avg_df['Segons'] = (avg_df['Timestamp'] - start_time).dt.total_seconds()
    
    numeric_cols = [c for c in dfs[0].columns if c != 'Timestamp']
    for col in numeric_cols:
        col_data = pd.concat([d[col] for d in dfs], axis=1)
        avg_df[col] = col_data.mean(axis=1)
        
    return avg_df

def plot_resources(df, fase, scenario_num, services, colors):
    fig, axs = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"Fase '{fase.upper()}' - Escenari {scenario_num} (Mètriques de recursos)\nMitjana aritmètica", 
                 fontsize=13, fontweight='bold', y=0.98)
    
    for idx, svc in enumerate(services):
        col = f"{svc}_RPS"
        if col in df.columns:
            axs[0].plot(df['Segons'], df[col], label=svc, color=colors[idx], linewidth=1.8)
    axs[0].set_title("Càrrega de trànsit per servei (Requests per segon)", fontsize=10, fontweight='bold')
    axs[0].set_ylabel("RPS")
    axs[0].grid(True, linestyle='--', alpha=0.5)
    
    for idx, svc in enumerate(services):
        col = f"{svc}_CPU_Usage"
        if col in df.columns:
            axs[1].plot(df['Segons'], df[col] * 1000, color=colors[idx], linewidth=1.8)
    axs[1].set_title("Consum del processador per servei", fontsize=10, fontweight='bold')
    axs[1].set_ylabel("CPU (milicores)")
    axs[1].grid(True, linestyle='--', alpha=0.5)
    
    for idx, svc in enumerate(services):
        col = f"{svc}_RAM_Usage"
        if col in df.columns:
            axs[2].plot(df['Segons'], df[col] / (1024**2), color=colors[idx], linewidth=1.8)
    axs[2].set_title("Ocupació de memòria RAM per servei", fontsize=10, fontweight='bold')
    axs[2].set_ylabel("RAM (MB)")
    axs[2].set_xlabel("Temps transcorregut (Segons)")
    axs[2].grid(True, linestyle='--', alpha=0.5)
    
    handles, labels = axs[0].get_legend_handles_labels()
    
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.93), 
               ncol=4, frameon=True, fontsize=9)
    
    plt.tight_layout(rect=[0, 0, 1, 0.90])
    output_img = f"results/grafica_{fase}_recursos_escenari{scenario_num}.png"
    plt.savefig(output_img, dpi=300, facecolor='white')
    plt.close(fig)

def plot_latencies_matrix(df, fase, scenario_num, services):
    fig, axs = plt.subplots(5, 2, figsize=(14, 16), sharex=False)
    fig.suptitle(f"Fase '{fase.upper()}' - Escenari {scenario_num} (Anàlisi de latències per microservei)\nPercentils P50, P95 i P99 - Mitjana aritmètica", 
                 fontsize=14, fontweight='bold', y=0.98)
    
    percentile_colors = {'P50': 'green', 'P95': 'orange', 'P99': 'red'}
    axes_flat = axs.flatten()

    latency_services = [s for s in services if s != "redis-cart"]
    
    for idx, svc in enumerate(latency_services):
        ax = axes_flat[idx]
        has_data = False
        
        for p in ['P50', 'P95', 'P99']:
            col_name = f"{svc}_Latency_{p}"
            if col_name in df.columns:
                ax.plot(df['Segons'], df[col_name], label=p, color=percentile_colors[p], linewidth=1.8)
                has_data = True

        replica_col = f"{svc}_Replics"
        if replica_col in df.columns:
            ax2 = ax.twinx()
            ax2.plot(df['Segons'], df[replica_col], label='Rèpliques', color='#1f77b4', linestyle=':', linewidth=2)
            ax2.set_ylabel("Rèpliques", fontsize=9, color='#1f77b4')
            ax2.tick_params(axis='y', labelcolor='#1f77b4')
            ymin, ymax = ax2.get_ylim()
            ax2.set_ylim(0, max(5, ymax * 1.1))
            has_data = True
        
        ax.set_title(f"{svc}", fontsize=11, fontweight='bold', color='black')
        ax.grid(True, linestyle='--', alpha=0.5)
        
        if idx % 2 == 0:
            ax.set_ylabel("Latència (ms)", fontsize=9)
            
        ax.set_xlabel("Temps (s)", fontsize=9)
            
        if has_data:
            lines, labels = ax.get_legend_handles_labels()
            if replica_col in df.columns:
                lines2, labels2 = ax2.get_legend_handles_labels()
                lines += lines2
                labels += labels2
            ax.legend(lines, labels, loc="upper left", frameon=True, fontsize=8)
        else:
            ax.text(0.5, 0.5, "Sense telemetria", color='gray', ha='center', va='center', transform=ax.transAxes)
            
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    output_img = f"results/grafica_{fase}_latencies_escenari{scenario_num}.png"
    plt.savefig(output_img, dpi=300, facecolor='white')
    plt.close(fig)

def extract_kpis(df, scenario_num, services, summary_list):
    if 'Segons' in df.columns:
        delta_t = df['Segons'].diff().fillna(0)
    else:
        delta_t = pd.Series([1.0] * len(df))

    for svc in services:
        kpis = {
            "Escenari": f"Escenari {scenario_num}",
            "Microservei": svc,
            "RPS_Mitjana": 0.0, "RPS_Max": 0.0,
            "P50_Mitjana_ms": 0.0, "P50_Max_ms": 0.0,
            "P95_Mitjana_ms": 0.0, "P95_Max_ms": 0.0,
            "P99_Mitjana_ms": 0.0, "P99_Max_ms": 0.0,
            "Errors_5xx_Max_RPS": 0.0,
            "CPU_Mitjana": 0.0, "CPU_Max": 0.0,
            "RAM_Mitjana": 0.0, "RAM_Max": 0.0,
            "Repliques_Mitjana": 1.0, "Repliques_Max": 1.0,
            "Cost_CPU_Min": 0.0,
            "Thrashing_Canvis_Abs": 0.0
        }
        
        if f"{svc}_RPS" in df.columns:
            kpis["RPS_Mitjana"] = round(df[f"{svc}_RPS"].mean(), 2)
            kpis["RPS_Max"] = round(df[f"{svc}_RPS"].max(), 2)
        if f"{svc}_Errors_5xx" in df.columns:
            kpis["Errors_5xx_Max_RPS"] = round(df[f"{svc}_Errors_5xx"].max(), 4)
            
        if f"{svc}_Latency_P50" in df.columns:
            kpis["P50_Mitjana_ms"] = round(df[f"{svc}_Latency_P50"].mean(), 1)
            kpis["P50_Max_ms"] = round(df[f"{svc}_Latency_P50"].max(), 1)
        if f"{svc}_Latency_P95" in df.columns:
            kpis["P95_Mitjana_ms"] = round(df[f"{svc}_Latency_P95"].mean(), 1)
            kpis["P95_Max_ms"] = round(df[f"{svc}_Latency_P95"].max(), 1)
        if f"{svc}_Latency_P99" in df.columns:
            kpis["P99_Mitjana_ms"] = round(df[f"{svc}_Latency_P99"].mean(), 1)
            kpis["P99_Max_ms"] = round(df[f"{svc}_Latency_P99"].max(), 1)
            
        if f"{svc}_CPU_Usage" in df.columns:
            kpis["CPU_Mitjana"] = round(df[f"{svc}_CPU_Usage"].mean() * 1000, 1)
            kpis["CPU_Max"] = round(df[f"{svc}_CPU_Usage"].max() * 1000, 1)
        if f"{svc}_RAM_Usage" in df.columns:
            kpis["RAM_Mitjana"] = round(df[f"{svc}_RAM_Usage"].mean() / (1024**2), 1)
            kpis["RAM_Max"] = round(df[f"{svc}_RAM_Usage"].max() / (1024**2), 1)

        replica_col = f"{svc}_Replics" 
        if replica_col in df.columns:
            kpis["Repliques_Mitjana"] = round(df[replica_col].mean(), 2)
            kpis["Repliques_Max"] = int(df[replica_col].max())
            
            cpu_requests_cores = {
                'frontend': 0.25, 'adservice': 0.1, 'cartservice': 0.04,
                'checkoutservice': 0.04, 'currencyservice': 0.08, 'emailservice': 0.015,
                'paymentservice': 0.01, 'productcatalogservice': 0.1, 'recommendationservice': 0.06,
                'shippingservice': 0.1, 'redis-cart': 0.07
            }
            req = cpu_requests_cores.get(svc, 0.1)
            cost_minutes = (df[replica_col] * req * delta_t).sum() / 60.0
            kpis["Cost_CPU_Min"] = round(cost_minutes, 3)
            
            rep_diff = df[replica_col].diff().dropna()
            kpis["Thrashing_Canvis_Abs"] = int(rep_diff.abs().sum())
            
        summary_list.append(kpis)

def main():
    if len(sys.argv) < 2:
        print("Ús: python3 scripts/generate_plots.py [FASE]   ex: control, hpa, rps")
        sys.exit(1)
        
    fase = sys.argv[1]
    
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", 
                "frontend", "paymentservice", "productcatalogservice", "recommendationservice", 
                "redis-cart", "shippingservice"]
                
    colors = ['#e31a1c', '#1f78b4', '#33a02c', '#ff7f00', '#6a3d9a', 
              '#b15928', '#fbb4ae', '#7fc97f', '#beaed4', '#fdc086', '#ffff99']
    
    all_kpis_summary = []
    
    os.makedirs("results", exist_ok=True)
    
    for s in range(1, 6):
        df = load_and_average_runs(fase, s)
        if df is not None:
            plot_resources(df, fase, s, services, colors)
            plot_latencies_matrix(df, fase, s, services)
            print(f"[Escenari {s}] Gràfiques de recursos i latències generades a 'results/'.")
            
            extract_kpis(df, s, services, all_kpis_summary)
            print(f"[Escenari {s}] Taula resum generada a 'results/'.")
            print("-" * 60)
            
    if all_kpis_summary:
        summary_df = pd.DataFrame(all_kpis_summary)
        output_csv = f"results/resum_kpis_fase_{fase}.csv"
        summary_df.to_csv(output_csv, index=False)
        print(f"\nEXTRACCIÓ COMPLETADA. S'ha generat el resum a: '{output_csv}'")
    else:
        print("\nNo s'ha generat cap taula perquè no s'han trobat dades vàlides per aquesta fase.")

if __name__ == "__main__":
    main()