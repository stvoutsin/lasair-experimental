FROM jupyter/scipy-notebook
ARG JUPYTERHUB_VERSION=0.8.0
RUN pip install --no-cache \
    jupyterhub==$JUPYTERHUB_VERSION

RUN pip install --upgrade pip


RUN pip install ipyaladin==0.1.6
RUN pip install plotly
RUN pip install notebook
RUN pip install pyvo
RUN pip install tqdm==4.31.1
RUN pip install hips==0.2
RUN pip install --pre astroquery
RUN pip install firethorn-utils
RUN pip install firethorn

RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix
RUN jupyter nbextension enable --py --sys-prefix ipyaladin
RUN jupyter nbextension enable --py plotlywidget --sys-prefix


