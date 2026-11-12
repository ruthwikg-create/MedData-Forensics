"""Run with `python start.py` on Windows or Linux. Creates DB on first launch."""
import os,uvicorn
if __name__=='__main__':
    host=os.getenv('MDF_HOST','127.0.0.1')
    port=int(os.getenv('MDF_PORT','8765'))
    print('MedData Forensics research software — not for clinical diagnosis')
    print(f'Open http://{host}:{port} in your browser')
    uvicorn.run('backend.api:app',host=host,port=port,log_level='info',reload=False)
