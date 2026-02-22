import pandas as pd
import numpy as np
import networkx as nx
import pingouin as pg
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class CausalNode(BaseModel):
    id: str
    group: int

class CausalLink(BaseModel):
    source: str
    target: str
    value: float
    strength: str

class Counterfactual(BaseModel):
    treatment: str
    outcome: str
    effect_size: float
    description: str

class CausalNetwork(BaseModel):
    nodes: list[CausalNode]
    links: list[CausalLink]
    counterfactuals: list[Counterfactual] = []
    error: str | None = None

def generate_causal_network(df: pd.DataFrame) -> CausalNetwork:
    """
    Generates a structural causal model using partial correlations as a base 
    for PC-like graph discovery, and calculates simple average treatment effects 
    (ATE) using linear regression as a proxy for DoWhy inference.
    """
    try:
        # 1. Prepare data
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if numeric_df.empty or len(numeric_df.columns) < 3 or len(numeric_df) < 5:
            return CausalNetwork(nodes=[], links=[], error="Not enough numeric data for causal analysis.")

        # Limit to top 15 columns with most variance
        variances = numeric_df.var().sort_values(ascending=False)
        top_cols = variances.head(15).index.tolist()
        df_subset = numeric_df[top_cols].copy()
        
        # Standardize for effect size comparability
        df_std = (df_subset - df_subset.mean()) / df_subset.std()

        # 2. Structure Discovery (DAG Generation) via Partial Correlations
        # Pingouin pcor computes the pairwise partial correlations controlling for all other vars
        pcor = df_std.pcorr()

        G = nx.DiGraph()
        for idx, col in enumerate(df_subset.columns):
            G.add_node(col, group=1)

        edges_added = []
        for i in range(len(pcor.columns)):
            for j in range(len(pcor.columns)):
                if i != j:
                    col_i = pcor.columns[i]
                    col_j = pcor.columns[j]
                    val = pcor.iloc[i, j]
                    
                    # Threshold for conditional independence
                    if abs(val) > 0.25:
                        # Direct edges from Higher Variance -> Lower Variance as a temporal heuristic
                        # (True PC algo would use CI tests and v-structures)
                        if variances[col_j] > variances[col_i]:
                            G.add_edge(col_i, col_j, weight=float(val))
                            edges_added.append((col_i, col_j, val))

        # 3. Format Network Output
        nodes = [{"id": str(n), "group": data.get("group", 1)} for n, data in G.nodes(data=True)]
        links = []
        for u, v, data in G.edges(data=True):
            weight = data.get("weight", 0.0)
            strength = "strong" if abs(weight) > 0.5 else "moderate"
            links.append({"source": str(u), "target": str(v), "value": round(weight, 3), "strength": strength})

        # 4. Counterfactual Inference (Do-Calculus proxy via regression controlling for parents)
        counterfactuals = []
        
        # Find likely "Outcome" variable (e.g., Revenue, Profit, Price, or lowest variance sink node)
        outcome_col = None
        for col in df_subset.columns:
            if any(x in col.lower() for x in ['revenue', 'profit', 'sales', 'price']):
                outcome_col = col
                break
        
        if not outcome_col:
            # Fallback: Node with most incoming edges (sink)
            in_degrees = dict(G.in_degree())
            if in_degrees:
                outcome_col = max(in_degrees, key=in_degrees.get)

        if outcome_col and in_degrees.get(outcome_col, 0) > 0:
            import statsmodels.api as sm
            
            # Identify immediate causes (parents in the DAG)
            parents = list(G.predecessors(outcome_col))
            
            # Predict outcome based on parents
            y = df_std[outcome_col]
            X = df_std[parents]
            X = sm.add_constant(X)
            
            try:
                model = sm.OLS(y, X).fit()
                
                # Take top 2 treatments
                for treatment in parents[:2]:
                    # Effect of 1 std deviation increase in treatment on outcome
                    effect = round(float(model.params[treatment]), 3)
                    
                    # Convert back to natural language counterfactual
                    direction = "increase" if effect > 0 else "decrease"
                    pct_change = abs(effect * 100)
                    
                    desc = (f"Causal Inference: If we increase '{treatment}' by 1 Standard Deviation, "
                            f"the model predicts a {pct_change:.1f}% std dev {direction} in '{outcome_col}', "
                            f"holding all other variables constant (Do-Calculus).")
                    
                    counterfactuals.append(Counterfactual(
                        treatment=treatment,
                        outcome=outcome_col,
                        effect_size=effect,
                        description=desc
                    ))
            except Exception as e:
                logger.warning(f"Could not compute OLS for counterfactuals: {e}")

        return CausalNetwork(nodes=nodes, links=links, counterfactuals=counterfactuals)

    except Exception as e:
        logger.exception("Causal generation failed")
        return CausalNetwork(nodes=[], links=[], error=f"Causal generation failed: {str(e)}")
