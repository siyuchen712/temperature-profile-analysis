import plotly.plotly as py
import plotly.graph_objs as go

def plot_profile(title, df, channels, tc_channel_names, gl = False):
    data_all = []
    for channel in channels:
        if tc_channel_names[channel]:
            tc_name = tc_channel_names[channel] + ' (' + channel.split(' ')[1] + ')'
        else:
            tc_name = channel
        if gl:
            channel_plot = go.Scattergl(
                                x = df.index,
                                y = df[channel],
                                mode = 'lines',
                                name = tc_name)
        else:
            channel_plot = go.Scatter(
                                x = df.index,
                                y = df[channel],
                                mode = 'lines',
                                name = tc_name)
        data_all.append(channel_plot)
    layout = dict(title = title,
              xaxis = dict(title = 'Time'),
              yaxis = dict(title = 'Temperature'))
    fig = dict(data=data_all, layout=layout)
    py.plot(fig, filename='scatter-mode')
