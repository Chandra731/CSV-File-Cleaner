import streamlit as st
import pandas as pd
from parser import load_file
from transformer import detect_column_types, parse_and_flatten_column, explode_list_column
from utils import suggest_transformations
from logger import TransformationLogger
from visuals import (
    plot_null_heatmap,
    plot_correlation_matrix,
    plot_categorical_distribution,
    plot_numeric_distribution,
    plot_outliers
)
import io

def main():
    st.title("Advanced Streamlit CSV Cleaner")

    # Dark mode toggle
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    dark_mode = st.sidebar.checkbox("Dark Mode", value=st.session_state.dark_mode)
    st.session_state.dark_mode = dark_mode

    if dark_mode:
        st.markdown("""
            <style>
            body { background-color: #121212; color: white; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body { background-color: white; color: black; }
            </style>
        """, unsafe_allow_html=True)

    st.sidebar.header("Upload your dataset")
    drag_drop_file = st.sidebar.file_uploader("Upload Or drag and drop your file here", 
                                               type=['csv', 'txt', 'xlsx', 'json', 'tsv', 'zip'], 
                                               key="dragdrop")
    url_input = st.sidebar.text_input("Or enter URL to raw file")

    # Load data
    if 'data' not in st.session_state or st.session_state.data is None:
        data = None
        if drag_drop_file is not None:
            data = load_file(drag_drop_file)
        elif url_input:
            data = load_file(url_input, from_url=True)
        st.session_state.data = data
    else:
        data = st.session_state.data

    if data is not None:
        st.write("Data preview:")
        st.dataframe(data.head())

        profiling = detect_column_types(data)

        st.subheader("Column Type Profiling")
        for col, info in profiling.items():
            st.markdown(f"**{col}**")
            st.write(f"Type distribution: {info['type_distribution']}")
            st.write(f"Mixed types: {info['mixed_types']}")
            st.write(f"Stringified objects: {info['stringified_objects']}")
            st.write(f"Null ratio: {info['null_ratio']:.2f}")
            if info['null_heavy']:
                st.warning(f"Column '{col}' is null-heavy (>50% nulls)")

        # Initialize logger if not exists
        if 'transformation_logger' not in st.session_state:
            st.session_state.transformation_logger = TransformationLogger()
        log = st.session_state.transformation_logger

        st.subheader("Column-wise Cleaning Options")
        selected_col = st.selectbox("Select column to clean", data.columns)

        # Drop column
        if st.checkbox(f"Drop column '{selected_col}'"):
            data = data.drop(columns=[selected_col])
            st.session_state.data = data
            st.success(f"Column '{selected_col}' dropped.")
            log.log(f"Drop column '{selected_col}'")

        # Rename column
        new_name = st.text_input(f"Rename column '{selected_col}' to", value=selected_col)
        if new_name != selected_col:
            data = data.rename(columns={selected_col: new_name})
            st.session_state.data = data
            st.success(f"Column '{selected_col}' renamed to '{new_name}'.")
            log.log(f"Rename column '{selected_col}' to '{new_name}'")
            selected_col = new_name

        # Convert data type
        dtype_choice = st.selectbox(f"Convert data type of '{selected_col}'", ['None', 'int', 'float', 'str', 'datetime'])
        if dtype_choice != 'None':
            try:
                if dtype_choice == 'datetime':
                    data[selected_col] = pd.to_datetime(data[selected_col], errors='coerce')
                else:
                    data[selected_col] = data[selected_col].astype(dtype_choice)
                st.session_state.data = data
                st.success(f"Converted '{selected_col}' to {dtype_choice}.")
                log.log(f"Convert '{selected_col}' to {dtype_choice}")
            except Exception as e:
                st.error(f"Failed to convert '{selected_col}': {e}")

        # Handle nulls
        null_handling = st.selectbox(f"Handle nulls in '{selected_col}'", 
                                     ['None', 'Drop rows', 'Fill with mean', 'Fill with median', 'Fill with mode', 'Fill with custom'])
        fill_val = None
        if null_handling == 'Drop rows':
            data = data.dropna(subset=[selected_col])
            st.session_state.data = data
            st.success(f"Dropped rows with nulls in '{selected_col}'.")
            log.log(f"Dropped rows with nulls in '{selected_col}'")
        elif null_handling.startswith("Fill"):
            if null_handling == 'Fill with custom':
                fill_val = st.text_input(f"Enter custom fill value for '{selected_col}'")
            elif null_handling == 'Fill with mean':
                fill_val = data[selected_col].mean()
            elif null_handling == 'Fill with median':
                fill_val = data[selected_col].median()
            elif null_handling == 'Fill with mode':
                fill_val = data[selected_col].mode().iloc[0] if not data[selected_col].mode().empty else None
            if fill_val is not None:
                data[selected_col] = data[selected_col].fillna(fill_val)
                st.session_state.data = data
                st.success(f"Filled nulls in '{selected_col}' with {fill_val}.")
                log.log(f"Filled nulls in '{selected_col}' with {fill_val}")

        # Parse/flatten complex values
        if st.checkbox(f"Parse and flatten complex values in '{selected_col}'"):
            data = parse_and_flatten_column(data, selected_col)
            st.session_state.data = data
            st.success(f"Parsed and flattened '{selected_col}'.")
            log.log(f"Parsed and flattened '{selected_col}'")

        # Explode lists/tuples
        if st.checkbox(f"Explode lists/tuples in '{selected_col}' into rows"):
            data = explode_list_column(data, selected_col)
            st.session_state.data = data
            st.success(f"Exploded lists/tuples in '{selected_col}'.")
            log.log(f"Exploded lists/tuples in '{selected_col}'")

        st.subheader("Smart Suggestions")
        for suggestion in suggest_transformations(profiling):
            st.info(suggestion)

        st.subheader("Transformation Log")
        log_text = log.get_log_text().replace('\\n', '\n')
        st.text_area("Transformation Steps", value=log_text, height=200)

        # Log export
        if st.button("Export Log as .txt"):
            log.export_log_txt("transformation_log.txt")
            st.success("Log exported as transformation_log.txt")

        if st.button("Export Log as .py"):
            log.export_log_py("transformation_log.py")
            st.success("Log exported as transformation_log.py")

        # Visualizations
        st.subheader("Visual Analytics")
        st.markdown("### Null Value Heatmap")
        plot_null_heatmap(data)

        st.markdown("### Correlation Matrix")
        corr_method = st.selectbox("Select correlation method", ['pearson', 'spearman'])
        numeric_data = data.select_dtypes(include=['number'])
        plot_correlation_matrix(numeric_data, method=corr_method, key="correlation_matrix")

        st.markdown("### Column Distribution")
        selected_col_dist = st.selectbox("Select column for distribution plots", data.columns)
        if pd.api.types.is_numeric_dtype(data[selected_col_dist]):
            plot_numeric_distribution(data, selected_col_dist, key=f"numeric_dist_{selected_col_dist}")
            plot_outliers(data, selected_col_dist, key=f"outliers_{selected_col_dist}")
        else:
            plot_categorical_distribution(data, selected_col_dist, key=f"categorical_dist_{selected_col_dist}")

        st.subheader("Export Options")
        export_format = st.selectbox("Select export format", ['csv', 'xlsx', 'json'])

        if st.button("Download Cleaned Dataset"):
            if export_format == 'csv':
                st.download_button("Download CSV", data.to_csv(index=False), file_name="cleaned_data.csv", mime="text/csv")
            elif export_format == 'xlsx':
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False)
                st.download_button("Download XLSX", buffer.getvalue(), file_name="cleaned_data.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            elif export_format == 'json':
                st.download_button("Download JSON", data.to_json(orient='records'), file_name="cleaned_data.json", mime="application/json")

        st.subheader("Export Profile Report")
        profile_report_option = st.selectbox("Select profile report type", ['None', 'pandas-profiling', 'ydata-profiling'])
        if profile_report_option != 'None':
            if st.button("Generate and Download Profile Report"):
                if profile_report_option == 'pandas-profiling':
                    from pandas_profiling import ProfileReport
                    profile = ProfileReport(data, minimal=True)
                elif profile_report_option == 'ydata-profiling':
                    from ydata_profiling import ProfileReport
                    profile = ProfileReport(data, minimal=True)
                profile.to_file("profile_report.html")
                with open("profile_report.html", "r", encoding="utf-8") as f:
                    html = f.read()
                st.download_button("Download Profile Report", data=html, file_name="profile_report.html", mime="text/html")

if __name__ == "__main__":
    main()
