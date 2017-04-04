import matplotlib.pyplot as plt

def profile_plot(profile, high_temp=95, low_temp=-40, tolerance=3,
                 y_limits = [ -50, 110 ], title="Thermal Profile", width=2):
    ''' This function assumes multi dataframe has board-named columns '''
    print('Plotting thermal profile...')
    df = profile.df[profile.channels]
    df.plot(kind='line', grid=True)
    plt.title(title)
    plt.ylim(y_limits)
    plt.axhline(y=high_temp-tolerance, linewidth=width,
                linestyle='dashed', color='r')
    plt.axhline(y=low_temp+tolerance,
                linewidth=width, linestyle='dashed', color='b')
    plt.xlabel('Time')
    plt.ylabel(u'Temperature (\N{DEGREE SIGN}C)')
    plt.legend( fontsize=10, loc='center left', bbox_to_anchor=(1.0, 0.5) )
    plt.tight_layout()
    plt.subplots_adjust(left=0.07, bottom=0.10, right=0.90,
                        top=0.95 , wspace=0.20, hspace=0.50)
    plt.show('hold')
    print('...plot complete.')
