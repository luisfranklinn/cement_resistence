"""Execute all article notebooks in order."""
import asyncio, sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os, time

analysis_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(analysis_dir)

notebooks = ['01_eda.ipynb', '02_model_training.ipynb', '03_results_figures.ipynb']

for nb_name in notebooks:
    print(f'\n{"="*50}')
    print(f'Executando: {nb_name}')
    t0 = time.time()
    nb_path = os.path.join(analysis_dir, nb_name)
    with open(nb_path, encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb, {'metadata': {'path': analysis_dir}})
        with open(nb_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
        print(f'OK — {(time.time()-t0)/60:.1f} min')
    except Exception as e:
        print(f'ERRO: {e}')
        sys.exit(1)

print('\nTodos os notebooks executados.')
