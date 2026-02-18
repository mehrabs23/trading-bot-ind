import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
from typing import List, Dict
from datetime import datetime

def calculate_drawdown(equity_curve: List[float]) -> float:
    if not equity_curve:
        return 0.0
    
    series = pd.Series(equity_curve)
    cum_max = series.cummax()
    drawdown = (series - cum_max) / cum_max
    return abs(drawdown.min())

def generate_html_report(stats: Dict, equity_curve: List[Dict], trades: List[Dict], filename: str):
    """
    Generates a standalone HTML report with equity curve and trade list.
    """
    
    # Prepare Data
    df_curve = pd.DataFrame(equity_curve)
    if not df_curve.empty:
        df_curve['timestamp'] = pd.to_datetime(df_curve['timestamp'])
        df_curve = df_curve.sort_values('timestamp')
        
    df_trades = pd.DataFrame(trades)
    
    # Calculate Drawdown
    max_dd = 0.0
    if not df_curve.empty:
        max_dd = calculate_drawdown(df_curve['equity'].tolist())
    
    # Create Equity Plot
    fig = go.Figure()
    if not df_curve.empty:
        fig.add_trace(go.Scatter(
            x=df_curve['timestamp'], 
            y=df_curve['equity'],
            mode='lines',
            name='Equity'
        ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Time',
        yaxis_title='Capital',
        template='plotly_dark'
    )
    
    plot_div = plot(fig, output_type='div', include_plotlyjs='cdn')
    
    # HTML Template
    html = f"""
    <html>
    <head>
        <title>Backtest Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1, h2 {{ color: #333; }}
            .metrics {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
            .metric {{ background: #eee; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
            .metric h3 {{ margin: 0 0 10px; font-size: 14px; color: #666; }}
            .metric p {{ margin: 0; font-size: 24px; font-weight: bold; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f8f8f8; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .win {{ color: green; }}
            .loss {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Backtest Performance Report</h1>
            <p>Generated on: {datetime.now()}</p>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Final Equity</h3>
                    <p>{stats.get('final_equity', 0):.2f}</p>
                </div>
                <div class="metric">
                    <h3>Total PnL</h3>
                    <p>{stats.get('realized_pnl', 0):.2f}</p>
                </div>
                <div class="metric">
                    <h3>Win Rate</h3>
                    <p>{stats.get('win_rate', 0)*100:.1f}%</p>
                </div>
                <div class="metric">
                    <h3>Max Drawdown</h3>
                    <p>{max_dd*100:.2f}%</p>
                </div>
                <div class="metric">
                    <h3>Total Trades</h3>
                    <p>{stats.get('num_trades', 0)}</p>
                </div>
            </div>
            
            <div class="chart">
                {plot_div}
            </div>
            
            <h2>Trade List</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th><th>Side</th><th>Entry</th><th>Exit</th><th>Qty</th><th>PnL</th><th>Reason</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for _, t in df_trades.iterrows():
        pnl_class = "win" if t['pnl_est'] > 0 else "loss"
        html += f"""
                    <tr>
                        <td>{t['symbol']}</td>
                        <td>{t['side']}</td>
                        <td>{t['entry']:.2f}</td>
                        <td>{t['exit']:.2f}</td>
                        <td>{t['qty']}</td>
                        <td class="{pnl_class}">{t['pnl_est']:.2f}</td>
                        <td>{t['reason']}</td>
                    </tr>
        """
        
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(filename, "w") as f:
        f.write(html)
    
    return filename
