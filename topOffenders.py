# Este script esta hecho para detectar los procesos mas pesados del sistema, topOffenders. Si un proceso esta consumiendo muhcho te notifica y te ofrece una accion:
# “kill suave” (SIGTERM) o “kill duro” (SIGKILL). Util para bajar prioridad con renice Útil para detectar leaks (navegador, Discord, etc.).

import os
import subprocess
import time
import signal
import psutil

# Flags para considerar un proceso "pesado"
CPU_FLAG = 50.0
MEM_FLAG = 500

# Segundos cada cuanto realiza el chequeo
CHECK_INTERVAL = 60

def get_top_processes():
    """Retorna el top5 de procesos por CPU y top5 por RAM"""
    procs = []
    
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    top_cpu = sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
    top_ram = sorted(procs, key=lambda x: x['memory_info'].rss if x['memory_info'] else 0, reverse=True)[:5]
    
    return top_cpu, top_ram
    
def print_top(top_cpu, top_ram):
    """"Printea los procesos en consola"""
    print("\n" + "="*55)
    print(f"  Monitor de procesos — {time.strftime('%H:%M:%S')}")
    print("="*55)
    
    print("\n TOP 5 por CPU:")
    for process in top_cpu:
        print(f"  PID {process['pid']:>6} | {process['name']:<25} | CPU: {process['cpu_percent']:.1f}%")

    print("\n TOP 5 por RAM:")
    for process in top_ram:
        ram_mb = process['memory_info'].rss / 1024 / 1024 if process['memory_info'] else 0
        print(f"  PID {process['pid']:>6} | {process['name']:<25} | RAM: {ram_mb:.1f} MB")
        
def check_offenders(top_cpu, top_ram):
    """Detecta procesos que superan las flags y ofrece acciones"""
    offenders = {}
    for process in top_cpu:
        if (process['cpu_percent'] or 0) >= CPU_FLAG:
            offenders[process['pid']] = process
    
    for process in top_ram:
        ram_mb = process['memory_info'].rss / 1024 / 1024 if process['memory_info'] else 0
        if ram_mb >= MEM_FLAG:
            offenders[process['pid']] = process
    
    for pid, process in offenders.items():
        ram_mb = process['memory_info'].rss / 1024 / 1024 if process['memory_info'] else 0
        print(f"\n⚠️  Proceso: '{process['name']}' (PID {pid})")
        print(f"   CPU: {process['cpu_percent']:.1f}%  |  RAM: {ram_mb:.1f} MB")
        print("   ¿Qué querés hacer?")
        print("   [1] Kill suave (SIGTERM)")
        print("   [2] Kill duro  (SIGKILL)")
        print("   [3] Bajar prioridad (renice +10)")
        print("   [4] Ignorar")
        
        try:
            choice = input("→ Opción: ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "4"
        
        if choice == "1":
            os.kill(pid, signal.SIGTERM)
            print(f"  SIGTERM enviado a PID {pid}")
        elif choice == "2":
            os.kill(pid, signal.SIGKILL)
            print(f"  SIGKILL enviado a PID {pid}")
        elif choice == "3":
            try:
                subprocess.run(["renice", "+10", "-p", str(pid)], check=True)
                print(f"  Prioridad bajada para PID {pid}")
            except subprocess.CalledProcessError as e:
                print(f"  Error al hacer renice: {e}")
        else:
            print("  Ignorado.")
        
def main():
    print("Script de monitoreo iniciado, el mismo chequeara cada 60 segundos... (Ctrl+C para detener)")
    for process in psutil.process_iter(['cpu_percent']):
        pass
    time.sleep(1)
    
    try:
        while True:
            top_cpu, top_ram = get_top_processes()
            print_top(top_cpu, top_ram)
            check_offenders(top_cpu, top_ram)
            print(f"\n Próximo chequeo en {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n Monitor detenido.")


if __name__ == "__main__":
    main()