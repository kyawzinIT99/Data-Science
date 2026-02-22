# back/services/forecast.py

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
from statsmodels.tsa.seasonal import seasonal_decompose
try:
    from prophet import Prophet
except ImportError:
    Prophet = None
from statsmodels.tsa.seasonal import seasonal_decompose
from app.utils.serialization import cleanup_serializable
import os


class PriceForecaster:
    def __init__(self, file_path: str, date_column: str = "Date", price_column: str = "Price"):
        self.file_path = file_path
        self.date_column = date_column
        self.price_column = price_column
        if Prophet:
            self.model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        else:
            self.model = None
        self.df = None
        self.monthly_df = None

    def load_data(self):
        """
        Load data and prepare monthly aggregated dataset.
        """
        if self.df is None:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"File not found: {self.file_path}")
            
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext == '.csv':
                try:
                    self.df = pd.read_csv(self.file_path)
                except Exception:
                    self.df = pd.read_csv(self.file_path, encoding='latin1')
            else:
                try:
                    self.df = pd.read_excel(self.file_path)
                except Exception:
                    try:
                        self.df = pd.read_excel(self.file_path, engine='openpyxl')
                    except Exception:
                        self.df = pd.read_excel(self.file_path, engine='xlrd')

        # Robust case-insensitive column search
        if self.date_column not in self.df.columns:
            matches = [c for c in self.df.columns if c.lower() == self.date_column.lower()]
            if matches:
                self.date_column = matches[0]
            else:
                matches = [c for c in self.df.columns if 'date' in c.lower() or 'time' in c.lower() or 'stamp' in c.lower()]
                if matches:
                    self.date_column = matches[0]
                else:
                    raise ValueError(f"Date column '{self.date_column}' not found")

        if self.price_column not in self.df.columns:
            matches = [c for c in self.df.columns if c.lower() == self.price_column.lower()]
            if matches:
                self.price_column = matches[0]
            else:
                matches = [c for c in self.df.columns if any(k in c.lower() for k in ['price', 'value', 'amount', 'val', 'revenue', 'sales'])]
                if matches:
                    self.price_column = matches[0]
                else:
                    raise ValueError(f"Price column '{self.price_column}' not found")

        # Convert date column with coercion to handle malformed dates
        self.df[self.date_column] = pd.to_datetime(self.df[self.date_column], errors='coerce')
        
        # Drop rows where date or price is null
        self.df = self.df.dropna(subset=[self.date_column, self.price_column])
        
        if len(self.df) == 0:
            raise ValueError("No valid data points found after cleaning")

        # Aggregate by month

        # Aggregate by month
        self.monthly_df = (
            self.df
            .groupby(pd.Grouper(key=self.date_column, freq="ME"))[self.price_column]
            .mean()
            .reset_index()
            .dropna()
        )

        # Create time index
        self.monthly_df["Month_Index"] = np.arange(len(self.monthly_df))

        return self.monthly_df

    def train_model(self):
        """
        Train Prophet model.
        """
        from app.services.analyzer import logger
        if self.monthly_df is None:
            raise ValueError("Data not loaded. Run load_data() first.")

        if not Prophet or not self.model:
            logger.warning("Prophet not available, skipping training.")
            return {"MAE": 0.0, "R2_Score": 0.0, "Model": "None"}

        prophet_df = self.monthly_df.rename(columns={
            self.date_column: 'ds', 
            self.price_column: 'y'
        })
        prophet_df = prophet_df[['ds', 'y']]

        # For very small datasets, disable yearly seasonality
        if len(prophet_df) < 24:
            self.model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)

        try:
            self.model.fit(prophet_df)
            forecast = self.model.predict(prophet_df)
            
            y_true = prophet_df['y'].values
            y_pred = forecast['yhat'].values

            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else 0.0

            return {
                "MAE": round(float(mae), 4),
                "R2_Score": round(float(r2), 4),
                "Model": "Prophet"
            }
        except Exception as e:
            logger.error(f"Prophet training failed: {e}")
            return {"MAE": 0.0, "R2_Score": 0.0, "Model": "Prophet (Failed)", "Error": str(e)}

    def predict_next_months(self, months: int = 3):
        """
        Predict future prices.
        """
        from app.services.analyzer import logger
        if self.monthly_df is None:
            raise ValueError("Data not loaded. Run load_data() first.")

        if not Prophet or getattr(self, 'model', None) is None:
            logger.warning("Prophet not available, skipping prediction.")
            return pd.DataFrame()

        try:
            future = self.model.make_future_dataframe(periods=months, freq='ME')
            forecast = self.model.predict(future)
            
            future_forecast = forecast.tail(months)
            
            forecast_df = pd.DataFrame({
                "Forecast_Date": future_forecast['ds'].dt.strftime('%Y-%m-%d'),
                "Predicted_Price": future_forecast['yhat'].round(2).tolist()
            })
            
            return forecast_df
        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            last_date = self.monthly_df[self.date_column].max()
            future_dates = pd.date_range(last_date + pd.offsets.MonthEnd(1), periods=months, freq="ME")
            last_price = self.monthly_df[self.price_column].iloc[-1]
            return pd.DataFrame({
                "Forecast_Date": [d.strftime('%Y-%m-%d') for d in future_dates],
                "Predicted_Price": [round(float(last_price), 2)] * months
            })

    def decompose_series(self, period: int = 12):
        """
        Decompose the monthly series into trend, seasonal, and residual components.
        """
        from app.services.analyzer import logger
        if self.monthly_df is None:
            raise ValueError("Data not loaded. Run load_data() first.")
        
        # statsmodels seasonal_decompose requires at least 2 * period
        actual_period = period
        if len(self.monthly_df) < 2 * actual_period:
            if len(self.monthly_df) >= 24: actual_period = 12
            elif len(self.monthly_df) >= 12: actual_period = 6
            elif len(self.monthly_df) >= 8: actual_period = 4
            elif len(self.monthly_df) >= 4: actual_period = 2
            else:
                logger.warning(f"Data too short for even minimal decomposition: {len(self.monthly_df)} months")
                return None

        # Set date as index
        series = self.monthly_df.set_index(self.date_column)[self.price_column]
        
        try:
            # Statsmodels needs a frequency, which monthly_df should have from pd.Grouper
            result = seasonal_decompose(series, model='additive', period=actual_period)
            
            decomposition = {
                "dates": self.monthly_df[self.date_column].dt.strftime('%Y-%m-%d').tolist(),
                "observed": result.observed.tolist(),
                "trend": result.trend.tolist(),
                "seasonal": result.seasonal.tolist(),
                "residual": result.resid.tolist()
            }
            
            # Clean up NaN values (statsmodels puts NaNs at the edges for moving averages)
            return cleanup_serializable(decomposition)
        except Exception as e:
            logger.error(f"Decomposition failed with period {actual_period}: {e}")
            return None


# ===============================
# Standalone Execution
# ===============================

if __name__ == "__main__":
    # Example usage
    FILE_PATH = "data.xlsx"  # <-- change to your actual Excel path

    forecaster = PriceForecaster(FILE_PATH)

    print("Loading data...")
    monthly_data = forecaster.load_data()

    print("Training model...")
    metrics = forecaster.train_model()
    print("Model Performance:", metrics)

    print("Predicting next 3 months...")
    forecast = forecaster.predict_next_months(3)

    print("\nForecast Results:")
    print(forecast)