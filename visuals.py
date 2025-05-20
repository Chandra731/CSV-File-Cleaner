import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

def plot_null_heatmap(df):
    """
    Plot heatmap of null values in the dataframe.
    """
    null_df = df.isnull()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(null_df, cbar=False, yticklabels=False, cmap='viridis', ax=ax)
    st.pyplot(fig)

def plot_correlation_matrix(df, method='pearson', key=None):
    """
    Plot correlation matrix heatmap using specified method.
    """
    corr = df.corr(method=method)
    fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', title=f'{method.capitalize()} Correlation Matrix')
    st.plotly_chart(fig, key=key)

def plot_categorical_distribution(df, col, key=None):
    """
    Plot pie chart or bar plot for categorical column.
    """
    counts = df[col].value_counts(dropna=False)
    if len(counts) <= 10:
        fig = px.pie(values=counts.values, names=counts.index, title=f'Distribution of {col}')
    else:
        fig = px.bar(x=counts.index, y=counts.values, title=f'Distribution of {col}')
    st.plotly_chart(fig, key=key)

def plot_numeric_distribution(df, col, key=None):
    """
    Plot histogram and boxplot for numeric column.
    """
    fig_hist = px.histogram(df, x=col, nbins=30, title=f'Histogram of {col}')
    st.plotly_chart(fig_hist, key=f"{key}_hist" if key else None)

    fig_box = px.box(df, y=col, title=f'Boxplot of {col}')
    st.plotly_chart(fig_box, key=f"{key}_box" if key else None)

def plot_outliers(df, col, key=None):
    """
    Simple outlier detection visualization using IQR method.
    """
    if not pd.api.types.is_numeric_dtype(df[col]):
        st.write(f"Column {col} is not numeric, skipping outlier plot.")
        return

    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]

    st.write(f"Number of outliers in {col}: {len(outliers)}")
    plot_numeric_distribution(df, col, key=key)
