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

        # load spot data
        df = None
        print("Extracting data...")
        for beam in plan.IonBeams:
            beamMetersetValue = beam.Meterset.Value
            totMetersetWeight = [cpp for cpp in beam.IonControlPoints][-1].MetersetWeight
            eParams = beam.GetEditableParameters()
            for controlPoint in eParams.IonControlPointPairs:
                df = pd.concat([df, pd.DataFrame({
                    'Field ID': beam.Id,
                    'X [mm]': [s.X for s in controlPoint.FinalSpotList],
                    'Y [mm]': [s.Y for s in controlPoint.FinalSpotList],
                    'MU': [s.Weight * (beamMetersetValue / totMetersetWeight) for s in controlPoint.FinalSpotList],
                })])

        # load structure data
        dfs = None
        for structure in plan.StructureSet.Structures:
            dvh = plan.GetDVHCumulativeData(
                structure,
                pyesapi.DoseValuePresentation.Relative,
                pyesapi.VolumePresentation.Relative,
                .1
            )
            if dvh is not None:
                dfs = pd.concat([dfs, pd.DataFrame({
                    'Structure ID': structure.Id,
                    'Color': "#" + structure.Color.ToString()[3:],  # format is '#AARRGGBB'
                    'Dose %': [p.DoseValue.Dose for p in dvh.CurveData],
                    'Volume %': [p.Volume for p in dvh.CurveData],
                })])
        
        # load target contour outline data
        dfc = None
        for beam in plan.Beams:
            beam_target = plan.StructureSet.StructuresLot(beam.TargetStructure.Id)
            for idx, contour in enumerate(beam.GetStructureOutlines(beam_target,True)):
                dfc = pd.concat([dfc, pd.DataFrame({
                    'Beam ID' : beam.Id,
                    'Structure ID': beam_target.Id,
                    'Color': "#" + beam_target.Color.ToString()[3:],
                    'Points X' : [p.X for p in contour],
                    'Points Y' : [p.Y for p in contour],
                    'Contour Idx' : idx,
                })])

    except Exception as e:
        raise e
    finally:
        print('Cleaning up...')
        _app.ClosePatient()
        _app.Dispose()
        print('Done!')

    return df, dfs, dfc

plan_title = f'Plan ID: {plan_id}\nPatient ID: {patient_id} | Course ID: {course_id}'
st.title(plan_title)

df, dfs, dfc = extract_data(patient_id, course_id, plan_id)
st.header('Raw Data')
st.download_button(
   "Download (.csv)",
   df.to_csv(index=False).encode('utf-8'),
   "raw_spot_data.csv",
   "text/csv",
   key='download-csv'
)
st.dataframe(df, use_container_width=True)

##
st.header('Spot Stats')
##
st.subheader('Beam MU')
##
st.dataframe(df.groupby('Field ID', as_index=False).agg({'MU': ['min', 'mean', 'max']}), use_container_width=True)

##
st.subheader('Plan MU')
##
goal_mu = st.number_input('Goal min MU', value=400, step=50, min_value=1)

spot_mus = df['MU'].to_numpy()
st.write(f"Spots above 100%: {np.count_nonzero(np.where(spot_mus > goal_mu))} / {len(spot_mus)}")
for mu_thresh_perc in [.05, .1, .2]:
    mu_thresh = goal_mu*(1-mu_thresh_perc)
    info = f"Spots below {100-mu_thresh_perc*100:.0f}%: "
    info += f"{np.count_nonzero(np.where((spot_mus > 0) & (spot_mus < mu_thresh)))}"
    st.write(info)

##
st.subheader('Beam Distances')
##
def distance_group(grp):
    x = grp['X [mm]'] - grp['X [mm]'].shift(1)
    y = grp['Y [mm]'] - grp['Y [mm]'].shift(1)
    grp['Spot Moves [mm]'] = np.sqrt(x**2 + y**2)
    return grp

df_dist = df.groupby('Field ID').apply(distance_group)

if int(pd.__version__.split('.')[0]) >= 2:
    # needed for later versions of pandas ¯\_(ツ)_/¯
    df_dist = df_dist.rename(columns={'Field ID':'Field Moves'}).reset_index()

st.dataframe(df_dist.groupby('Field ID', as_index=False).agg({'Spot Moves [mm]': ['min','mean','max']}), use_container_width=True)

##
st.subheader('MU Histograms')
##
bin_size = st.number_input('Bin width', value=75, step=25, min_value=1)
try:
    group_labels = df['Field ID'].unique()
    hist_data = [df[df['Field ID'] == f_id]['MU'] for f_id in group_labels]
    # TODO: switch y-axis to counts
    fig_hist = ff.create_distplot(hist_data, group_labels, histnorm='', bin_size=bin_size)
    st.plotly_chart(fig_hist, use_container_width=True)

except np.linalg.LinAlgError:
    st.write('Fields have identicial MUs. Cannot plot histogram.')

##
st.header('Spot Positions and MUs')
##
px.defaults.color_continuous_scale = px.colors.sequential.Burg  #Brwnyl

for grp_name, grp_df in df.groupby('Field ID'):
    # TODO: add PTV contour (beam target)

    fig_scatt = px.scatter(grp_df, x='X [mm]', y='Y [mm]', color='MU', hover_data=['MU'], title=grp_name)
    fig_scatt.add_trace(go.Scatter(
        x=grp_df['X [mm]'], y=grp_df['Y [mm]'],
        mode='lines', line_dash='dash', line_color= 'black', name='path'
    ))
    fig_scatt.update_traces(marker=dict(size=20), selector=dict(mode='markers'))
    fig_scatt.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    for _, dfc_field in dfc[dfc['Beam ID'] == grp_name].groupby('Contour Idx'):
        structure_id = dfc_field['Structure ID'][0]
        fig_scatt.add_trace(go.Scatter(
            x=dfc_field['Points X'], y=dfc_field['Points Y'], mode='lines',
            name=structure_id
        ))
        fig_scatt.update_traces(line_color=dfc_field['Color'][0], selector=dict(name='PTV'))

    st.plotly_chart(fig_scatt, use_container_width=True)

##
st.header('DVH')
##
dvh_fig = go.Figure()
for structure_id, dvh_data in dfs.groupby('Structure ID'):
    dvh_fig.add_trace(go.Scatter(
        x=dvh_data['Dose %'], y=dvh_data['Volume %'], mode='lines', line_color=dvh_data['Color'][0], name=structure_id
    ))
dvh_fig.update_layout(
    paper_bgcolor='black',
    plot_bgcolor='black',
    legend=dict(
        font=dict(color='white')
    ),
    title = dict(
        text=plan_title,
        font=dict(color='white')
    ),
    yaxis = dict(
        title='Volume [%]',
        gridcolor='grey'
    ),
    xaxis = dict(
        title = 'Dose [%]',
        showgrid=True,
        gridcolor='grey',
    )
)

st.plotly_chart(dvh_fig, use_container_width=True)