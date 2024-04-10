import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
from dataclasses import asdict
from risk_adjustment_model import MedicareModelV24, MedicareModelV28


st.set_page_config(page_title="Medicare Risk Adjustment Model Runner")


def display_score_results(result):
    score_results = {
        "Adjusted": {
            "Score": result.score,
            "Disease Score": result.disease_score,
            "Demographic Score": result.demographic_score,
        },
        "Unadjusted": {
            "Score": result.score_raw,
            "Disease Score": result.disease_score_raw,
            "Demographic Score": result.demographic_score_raw,
        },
    }

    st.write("Scores Table")
    df = pd.DataFrame.from_dict(score_results, orient="index")
    st.write(df)


def display_category_details(category_details):
    st.write("Category Details Table")
    df = pd.DataFrame.from_dict(category_details, orient="index")
    st.write(df)


def score_comparison(result):
    score = result.score
    unadjusted_score = result.score_raw

    fig = go.Figure()

    # Adding the 'Unadjusted Score' bar
    fig.add_trace(
        go.Bar(
            x=["Unadjusted Score"],
            y=[unadjusted_score],
            name="Unadjusted Score",
            marker_color="lightsalmon",
        )
    )

    # Adding the 'Score' bar
    fig.add_trace(
        go.Bar(x=["Score"], y=[score], name="Score", marker_color="indianred")
    )

    fig.update_layout(
        title_text="Unadjusted Score vs Score",
        xaxis=dict(title="Score Type"),
        yaxis=dict(title="Score"),
        barmode="group",
    )

    return fig


def score_breakdown(result):
    disease_score_pct = round(result.disease_score / result.score, 3)
    demographic_score_pct = 1 - disease_score_pct

    categories = ["Score"]
    hover_template1 = (
        f"Value: %{{y}}<br>Pct of Score: {disease_score_pct*100}%<extra></extra>"
    )
    hover_template2 = (
        f"Value: %{{y}}<br>Pct of Score: {demographic_score_pct*100}%<extra></extra>"
    )
    # Create traces
    fig = go.Figure(
        data=[
            go.Bar(
                name="Disease Score",
                x=categories,
                y=[result.disease_score],
                hovertemplate=hover_template1,
                # text=disease_score_pct,
            ),
            go.Bar(
                name="Demographic Score",
                x=categories,
                y=[result.demographic_score],
                hovertemplate=hover_template2,
                # text=demographic_score_pct,
            ),
        ]
    )

    # Change the bar mode to stack
    fig.update_layout(
        barmode="stack",
        title="Disease vs Demographic Score",
    )

    return fig


def display_score_breakdown(result):
    fig1 = score_comparison(result)
    fig2 = score_breakdown(result)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.plotly_chart(fig2, use_container_width=True)


def display_score_breakdown_pct(result):
    disease_score_pct = round(result.disease_score / result.score, 3)
    demographic_score_pct = 1 - disease_score_pct

    # Labels for the pie chart segments
    labels = ["Disease Score", "Demographic Score"]

    # Values for each segment
    values = [disease_score_pct, demographic_score_pct]

    # Creating the pie chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])

    # Update the layout for a clear visualization
    fig.update_layout(title_text="Scores Proportion")

    # Display the figure in the Streamlit app
    st.plotly_chart(fig)


def download_results(results):
    result_dict = asdict(results)
    json_str = json.dumps(result_dict, indent=4)

    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name="results.json",
        mime="application/json",
    )


def main():
    # Title for the app
    st.title("Risk Adjustment Model Runner")

    st.markdown("""
        This is a webapp to run the risk adjustment models found in the PyPI project [risk_adjustment_model](https://pypi.org/project/risk_adjustment_model/).
        Please see the PyPI page for more details about the model if you have questions.

        If an issue is found with the scoring results, please submit an here on the [risk_adjustment_model Github page](https://github.com/pfehlinger/risk_adjustment_model).

        For issues or ideas related to the webapp, please submit an issue on the [webapp Github page](https://github.com/pfehlinger/risk_adjustment_model_webapp).

        Note: A github account is required to submit issues

        Please see sidebar to set parameters and press the button to calculate score.

        ## Scoring Results
    """)

    with st.sidebar:
        # User inputs
        st.markdown("""
        ## Model Selection

        Choose which model you would like to run. Options are:
        - V24: 2020 CMS Community Model
        - V28: 2024 CMS Community Model
        """)
        model_version = st.selectbox("Model Verison", ["V24", "V28"])

        st.markdown("""
        ## Model Inputs

        Enter the inputs to run the Medicare Risk Adjustment Model.
        """)

        gender = st.selectbox("Gender", ["M", "F"])

        st.markdown(
            "[OREC Definition and Values](https://resdac.org/cms-data/variables/medicare-original-reason-entitlement-code-orec)"
        )
        orec = str(st.number_input("OREC", min_value=0, max_value=3, step=1))

        age = st.number_input("Age", min_value=0, step=1)
        medicaid = st.selectbox("Medicaid", [True, False])
        diagnosis_codes = st.text_input("Diagnosis Codes (comma-separated)")
        year = st.number_input("Year", min_value=2020, step=1)

        st.markdown("""
        Here are the definitions for the population values:
        - CNA - Community, Non Dual, Aged (default)
        - CND - Community, Non Dual, Disabled
        - CPA - Community, Partial Dual, Aged
        - CPD - Community, Partial Dual, Disabled
        - CFA - Community, Full Dual, Aged
        - CFD - Community, Full Dual, Disabled
        - INS - Institutional
        - NE - CMS New Enrollee
        """)
        population = st.selectbox(
            "Population",
            [
                "CNA",
                "CND",
                "CPA",
                "CPD",
                "CFA",
                "CFD",
                "INS",
                "NE",
            ],
        )

        calculate = st.button("Calculate")

    # Button to calculate the result
    if calculate:
        # Assuming diagnosis_codes are expected as a list in your model
        diagnosis_codes_list = diagnosis_codes.split(",")

        if model_version == "V24":
            # Initialize the model with user inputs
            model = MedicareModelV24(year=year)
        else:
            model = MedicareModelV28(year=year)

        # Assuming your model has a method to calculate the score
        result = model.score(
            gender=gender,
            orec=orec,
            age=age,
            medicaid=medicaid,
            population=population,
            diagnosis_codes=diagnosis_codes_list,
            verbose=True,
        )

        # Displaying the result
        display_score_results(result)
        display_category_details(result.category_details)
        display_score_breakdown(result)
        download_results(result)


if __name__ == "__main__":
    main()
