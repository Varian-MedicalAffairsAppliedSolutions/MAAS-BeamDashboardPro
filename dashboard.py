import streamlit as st
import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go
import argparse


@st.cache_data
def parse_args():
    parser = argparse.ArgumentParser(
                    prog='dashboard',
                    description='PLAID Dashboard to review results of FLASH optimizations',
                    epilog='v0.1.0')
    parser.add_argument('--plan-id', required=True)
    parser.add_argument('--course-id', required=True)
    parser.add_argument('--patient-id', required=True)

    return parser.parse_args()

args = parse_args()

plan_id = args.plan_id  #"MODev01"
course_id = args.course_id  #"Min MU 400"
patient_id = args.patient_id  #"LUNG_063"


@st.cache_data
def extract_data(patient_id, course_id, plan_id):
    print("Launching PyESAPI...")
    import pyesapi
    
    print("Creating ESAPI app instance...")
    _app = pyesapi.CustomScriptExecutable.CreateApplication('dashboard_pro')
    
    try:
        patient = _app.OpenPatientById(patient_id)
        plan = patient.CoursesLot(course_id).IonPlanSetupsLot(plan_id)

        df = None
        spot_idx = 0
        print("Extracting data...")
        for beam in plan.IonBeams:
            beamMetersetValue = beam.Meterset.Value;
            totMetersetWeight = [cpp for cpp in beam.IonControlPoints][-1].MetersetWeight;
            eParams = beam.GetEditableParameters();
            for controlPoint in eParams.IonControlPointPairs:
                for spot in controlPoint.FinalSpotList:
                    spot_dict = {
                        'Spot Idx': [spot_idx],
                        'Field ID': [beam.Id],
                        'X [mm]': [spot.X],
                        'Y [mm]': [spot.Y],
                        'MU': [spot.Weight * (beamMetersetValue / totMetersetWeight)]
                    }
                    if df is not None:
                        df = pd.concat([df, pd.DataFrame(spot_dict)])
                    else:
                        df = pd.DataFrame(spot_dict)
                    spot_idx += 1
    except Exception as e:
        raise e
    finally:
        print('Cleaning up...')
        _app.ClosePatient()
        _app.Dispose()
        print('Done!')

    df.set_index('Spot Idx')
    return df

st.title(f'Plan ID: {plan_id}\nPatient ID: {patient_id} | Course ID: {course_id}')

df = extract_data(patient_id, course_id, plan_id)
st.dataframe(df)

st.header('Spot Stats')
st.dataframe(df.groupby('Field ID', as_index=False).agg({'MU': ['min', 'mean', 'max']}), use_container_width=True)

def distance_group(grp):
    x = grp['X [mm]'] - grp['X [mm]'].shift(1)
    y = grp['Y [mm]'] - grp['Y [mm]'].shift(1)
    grp['Spot Moves [mm]'] = np.sqrt(x**2 + y**2)
    return grp

df_dist = df.groupby('Field ID').apply(distance_group)

if int(pd.__version__.split('.')[0]) >= 2:
    # needed for later versions of pandas ¯\_(ツ)_/¯
    df_dist = df_dist.rename(columns={'Field ID':'Field Moves'}).reset_index()

st.dataframe(df_dist.groupby('Field ID', as_index=False).agg({'Spot Moves [mm]': ['min','mean','max']}))

try:
    group_labels = df['Field ID'].unique()
    hist_data = [df[df['Field ID'] == f_id]['MU'] for f_id in group_labels]
    fig_hist = ff.create_distplot(hist_data, group_labels)
    st.header('MU Histograms')
    st.plotly_chart(fig_hist, use_container_width=True)

except np.linalg.LinAlgError:
    st.write('Fields have identicial MUs. Cannot plot histogram.')

st.header('Spot Positions and MUs')
px.defaults.color_continuous_scale = px.colors.sequential.Burg  #Brwnyl
for grp_name, grp_df in df.groupby('Field ID'):
    # fig_scatt = go.Figure()

    fig_scatt = px.scatter(grp_df, x='X [mm]', y='Y [mm]', color='MU', hover_data=['MU'])
    fig_scatt.add_trace(go.Scatter(x=grp_df['X [mm]'], y=grp_df['Y [mm]'], mode='lines', name=grp_name))
    fig_scatt.update_traces(marker=dict(size=20), selector=dict(mode='markers'))
    fig_scatt.update_traces(line_dash='dash', selector=dict(type='scatter'))
    fig_scatt.update_traces(line_color='black', selector=dict(type='scatter'))
    fig_scatt.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    st.plotly_chart(fig_scatt, use_container_width=True)