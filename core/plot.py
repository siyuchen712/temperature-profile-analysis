import plotly.plotly as py
import plotly.graph_objs as go

def plot_profile(title, df, channels):
    data_all = []
    for channel in channels:
        channel_plot = go.Scatter(
                            x = df.index,
                            y = df[channel],
                            mode = 'lines',
                            name = channel)
        data_all.append(channel_plot)
    layout = dict(title = title,
              xaxis = dict(title = 'Time'),
              yaxis = dict(title = 'Temperature'))
    fig = dict(data=data_all, layout=layout)
    py.plot(fig, filename='scatter-mode')
