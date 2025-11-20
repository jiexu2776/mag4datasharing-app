import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pyrolite.geochem.norm import get_reference_composition
from pyrolite.plot.spider import spider
import requests

st.title('How to build an App around your dataset')

if st.user.is_logged_in:
    st.sidebar.success("You are logged in with ORCID")
else:
    st.sidebar.error('You are not loged in to ORCID')

if st.sidebar.button("Log out"):
    st.logout()





# ------ Functions
def get_metadata(repo_owner, repo_name, folder, file_name):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder}/{file_name}.json'
    github_token = st.secrets['GitHub_Token']
    headers = {'Authorization': f'Bearer {github_token}'}
    response = requests.get(url, headers=headers)
    file_url = response.json()['download_url']
    file_content_response = requests.get(file_url, headers=headers)
    return file_content_response.json()

@st.cache_data
def get_csv_urls(repo_owner, repo_name, folder):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder}'
    github_token = st.secrets['GitHub_Token']
    headers = {'Authorization': f'Bearer {github_token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        files = [file for file in response.json() if file['name'].endswith('.csv')]
        
        # Fetch and store the contents of each JSON file
        file_urls = {}
        for file in files:
            file_urls[file['name'].split('.')[0]] = file['download_url']
        return file_urls
    else:
        return f"Error: Unable to fetch files. Status code: {response.status_code}"

st.title('Browse Dataset Info & Content')

# 1. Load metadata for all datasets
df_metadata = pd.read_csv(
    'https://raw.githubusercontent.com/jiexu2776/mag4datasets/main/overview_available_datasets.csv'
)

tab1, tab2 = st.tabs(['All Datasets', 'Select & Explore a Dataset'])

# -------------------------------------------------------------------
# TAB 1 – just show the metadata table
# -------------------------------------------------------------------
with tab1:
    st.dataframe(df_metadata)

# -------------------------------------------------------------------
# TAB 2 – select a dataset and then make plots
# -------------------------------------------------------------------
with tab2:
    st.subheader("Select a Dataset")

    # Build mapping Title -> Short Title (or whatever key you use)
    # Adjust column names here if needed
    titles = df_metadata["Title"].dropna().sort_values()
    sel_title = st.selectbox(
        'Select a dataset',
        titles,
        index=None,
        placeholder='click to select a dataset'
    )

    if sel_title is None:
        st.write("Select a dataset to see details and create plots.")
    else:
        # Get the metadata row for this title
        row = df_metadata.loc[df_metadata["Title"] == sel_title].iloc[0]
        dataset_key = row["Short Title"]   # adjust if your key column is named differently

        # Show metadata for this dataset (using your helper)
        dataset_metadata = get_metadata(
            "jiexu2776", "mag4datasets", "metadata", dataset_key
        )
        st.markdown("### Dataset metadata")
        st.table(dataset_metadata)

        # 2. Load the corresponding data file
        base_url = "https://raw.githubusercontent.com/jiexu2776/mag4datasets/main/data/"
        data_url = base_url + f"{dataset_key}.csv"

        try:
            df_data = pd.read_csv(data_url)
        except Exception as e:
            st.error(f"Could not load data file for this dataset: {e}")
            st.stop()

        st.markdown("### Data preview")
        st.dataframe(df_data.head())

        # 3. Tabs for plots on this selected dataset
        plot_tab1, plot_tab2 = st.tabs(["🕷️ Pyrolite Spider / REE Plot", "📊 Interactive Scatter"])

        # ==========================================================
        # PLOT TAB 1 – Pyrolite spider / REE plot
        # ==========================================================
        with plot_tab1:
            st.markdown("#### Pyrolite Spider / REE Plot")

            # Select sample ID column
            sample_col = st.selectbox(
                "Sample ID column:",
                options=df_data.columns,
                index=0
            )

            # Select element columns
            st.markdown("Select element columns for the spider/REE plot")

            typical_ree = ["La", "Ce", "Pr", "Nd", "Sm", "Eu",
                           "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]
            available_ree = [c for c in typical_ree if c in df_data.columns]

            default_elements = available_ree if available_ree else [
                c for c in df_data.select_dtypes(include="number").columns
                if c != sample_col
            ]

            element_cols = st.multiselect(
                "Element columns (in plotting order):",
                options=[c for c in df_data.columns if c != sample_col],
                default=default_elements
            )

            if element_cols:
                # Choose samples
                samples = df_data[sample_col].astype(str).unique().tolist()
                selected_samples = st.multiselect(
                    "Samples to plot:",
                    options=samples,
                    default=samples[:3]
                )

                # Normalisation (via pyrolite reference compositions)
                ref_options = {
                    "None (no normalisation)": None,
                    "Primitive Mantle (Palme & O'Neill 2014)": "PM_PON",
                    "Chondrite (PON)": "Chondrite_PON",
                }
                ref_choice = st.selectbox(
                    "Normalise to:",
                    options=list(ref_options.keys()),
                    index=0
                )

                ref_comp = None
                if ref_options[ref_choice] is not None:
                    ref_comp_name = ref_options[ref_choice]
                    ref_comp = get_reference_composition(ref_comp_name)

                if selected_samples:
                    fig, ax = plt.subplots(figsize=(7, 4))

                    for s in selected_samples:
                        row_s = df_data[df_data[sample_col].astype(str) == str(s)]
                        if row_s.empty:
                            continue

                        values = row_s[element_cols].iloc[0]
                        sample_df = pd.DataFrame(
                            [values.values],
                            columns=element_cols,
                            index=[s]
                        )

                        if ref_comp is not None:
                            # align reference to selected elements; reference has index = elements
                            ref_vals = ref_comp.loc[element_cols, "value"]
                            norm_df = sample_df.divide(ref_vals.values, axis=1)
                        else:
                            norm_df = sample_df

                        spider(
                            norm_df,
                            ax=ax,
                            labels=element_cols,
                            label=s
                        )

                    ax.set_xlabel("Element")
                    ax.set_ylabel(
                        "Normalised value" if ref_comp is not None else "Value"
                    )
                    ax.set_yscale("log")
                    ax.legend()
                    ax.grid(True, which="both", linestyle="--", alpha=0.3)

                    st.pyplot(fig)
                else:
                    st.info("Select at least one sample to plot.")
            else:
                st.info("Select at least one element column to plot.")

        # ==========================================================
        # PLOT TAB 2 – Interactive scatter (no pyrolite needed)
        # ==========================================================
        with plot_tab2:
            import plotly.express as px

            st.markdown("#### Interactive scatter plot")

            numeric_cols = df_data.select_dtypes(include="number").columns.tolist()
            if len(numeric_cols) < 2:
                st.warning("This dataset doesn’t have enough numeric columns for a scatter plot.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    x_col = st.selectbox("X-axis:", options=numeric_cols, index=0)
                with col2:
                    y_col = st.selectbox(
                        "Y-axis:",
                        options=[c for c in numeric_cols if c != x_col],
                        index=0
                    )

                color_col = st.selectbox(
                    "Colour by (optional):",
                    options=["(none)"] + df_data.columns.tolist(),
                    index=0
                )

                hover_col = st.selectbox(
                    "Hover label (optional):",
                    options=["(none)"] + df_data.columns.tolist(),
                    index=(
                        df_data.columns.tolist().index(sample_col) + 1
                        if sample_col in df_data.columns
                        else 0
                    )
                )

                scatter_kwargs = {"x": x_col, "y": y_col}
                if color_col != "(none)":
                    scatter_kwargs["color"] = color_col
                if hover_col != "(none)":
                    scatter_kwargs["hover_data"] = [hover_col]

                fig_scatter = px.scatter(df_data, **scatter_kwargs)
                st.plotly_chart(fig_scatter, use_container_width=True)
