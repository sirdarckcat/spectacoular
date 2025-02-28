# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Example that demonstrates different beamforming algorithms
"""
from os import path
from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models.tools import BoxEditTool
from bokeh.models import LinearColorMapper,ColorBar,ColumnDataSource, Range1d, HoverTool, Spacer
from bokeh.models.widgets import Panel,Tabs,Select, Toggle, RangeSlider,Div, Paragraph,\
    NumberFormatter
from bokeh.plotting import figure
from bokeh.palettes import viridis, Spectral11
from bokeh.server.server import Server
from numpy import array, nan, zeros
import acoular
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerFunctional,BeamformerCapon,\
BeamformerEig,BeamformerMusic,BeamformerDamas,BeamformerDamasPlus,BeamformerOrth,\
BeamformerCleansc, BeamformerClean, BeamformerPresenter,\
BeamformerCMF,BeamformerGIB,Environment,Calib,set_calc_button_callback


COLORS = list(Spectral11)
doc = curdoc() 

#%% Build processing chain
micgeofile = path.join( path.split(acoular.__file__)[0],'xml','array_56.xml')
tdfile = 'example_data.h5'
calibfile = 'example_calib.xml'
ts = MaskedTimeSamples(name=tdfile)
cal = Calib(from_file=calibfile)
ts.start = 0 # first sample, default
ts.stop = 16000 # last valid sample = 15999
invalid = [1,7] # list of invalid channels (unwanted microphones etc.)
ts.invalid_channels = invalid 
ts.calib = cal
mg = MicGeom(from_file=micgeofile,invalid_channels = invalid)
ps = PowerSpectra(time_data=ts,block_size=1024,overlap="50%")
rg = RectGrid(x_min=-0.6, x_max=-0.0, y_min=-0.3, y_max=0.3, z=0.68,increment=0.01)
env = Environment(c = 346.04)
st = SteeringVector( grid = rg, mics=mg, env=env )    

#%%  Beamforming Algorithms
bb = BeamformerBase( freq_data=ps, steer=st )  
bf = BeamformerFunctional( freq_data=ps, steer=st, gamma=4)
bc = BeamformerCapon( freq_data=ps, steer=st )  
be = BeamformerEig( freq_data=ps, steer=st, n=54)
bm = BeamformerMusic( freq_data=ps, steer=st, n=6)   
bd = BeamformerDamas(beamformer=bb, n_iter=100)
bdp = BeamformerDamasPlus(beamformer=bb, n_iter=100)
bo = BeamformerOrth(beamformer=be, eva_list=list(range(38,54)))
bs = BeamformerCleansc(freq_data=ps, steer=st, r_diag=True)
bl = BeamformerClean(beamformer=bb, n_iter=100)
bcmf = BeamformerCMF(freq_data=ps, steer=st, method='LassoLarsBIC')
bgib = BeamformerGIB(freq_data=ps, steer=st, method= 'LassoLars', n=10)

#%% Beamformer selector

beamformer_dict = {
    'Conventional Beamforming': (bb, bb.get_widgets()),
    'Functional Beamforming': (bf, bf.get_widgets()),
    'Capon Beamforming': (bc, bc.get_widgets()),
    'Eigenvalue Beamforming': (be, be.get_widgets()),
    'Music Beamforming': (bm, bm.get_widgets()),
    'Damas Deconvolution': (bd, bd.get_widgets()),
    'DamasPlus Deconvolution': (bdp, bdp.get_widgets()),
    'Orthogonal Beamforming': (bo, bo.get_widgets()),
    'CleanSC Deconvolution': (bs, bs.get_widgets()),
    'Clean Deconvolution': (bl, bl.get_widgets()),
    'CMF': (bcmf, bcmf.get_widgets()),
    'GIB': (bgib, bgib.get_widgets()),
}

# create Select Button to select Beamforming Algorithm
beamformerSelector = Select(title="Beamforming Method:",
                        options=list(beamformer_dict.keys()),
                        value=list(beamformer_dict.keys())[0],
                        height=75)

# use additional classes for data evaluation/view
bv = BeamformerPresenter(source=bb,num=3,freq=4000.)
bv.trait_widget_args.update(num={'width':40},freq={'width':100})
# get widgets to control settings
tsWidgets = ts.get_widgets()
tsWidgets['invalid_channels'].height = 100 
tsWidgets['invalid_channels'].width = 300 
tsWidgets['invalid_channels'].editable = False 
mgWidgets = mg.get_widgets()
mgWidgets['invalid_channels'].height = 100 
mgWidgets['invalid_channels'].width = 300 
mgWidgets['invalid_channels'].editable = False 
mgWidgets['mpos_tot'].width = 300 
mgWidgets['mpos_tot'].editable = False 
envWidgets = env.get_widgets()
calWidgets = cal.get_widgets()
psWidgets = ps.get_widgets()
rgWidgets = rg.get_widgets()
stWidgets = st.get_widgets()
bbWidgets = bb.get_widgets()
bvWidgets = bv.get_widgets()

formatter = NumberFormatter(format="0.00")
for f in mgWidgets['mpos_tot'].columns:
    f.formatter = formatter

settings_dict = {
    "Time Data": tsWidgets,
    "Microphone Geometry": mgWidgets,
    "Environment": envWidgets,
    "Calibration": calWidgets,
    "FFT/CSM": psWidgets,
    "Focus Grid": rgWidgets,
    "Steering Vector": stWidgets,
    "Beamforming Method": bbWidgets,
}

#%% Widgets for display

colorMapper = LinearColorMapper(palette=viridis(100), 
                              low=40, high=50 ,low_color=(1,1,1,0))
dynamicSlider = RangeSlider(start=0, end=120, step=1., value=(40,50),
                            width=220,height=50,
                            title="Dynamic Range")
def dynamicSlider_callback(attr, old, new):
    (colorMapper.low, colorMapper.high) = dynamicSlider.value
dynamicSlider.on_change("value",dynamicSlider_callback)

# create Button to trigger beamforming result calculation
calcButton = Toggle(label="Calculate",button_type="primary", width=175,height=75)
set_calc_button_callback(bv.update,calcButton)

RED = "#961400"
BLUE = "#3288bd"

# beamformerPlot
bfplotwidth = 700
bfPlot = figure(title='Source Map', 
                tools = 'pan,wheel_zoom,reset', 
                #tooltips=bftooltips,
                width=bfplotwidth,
                height=700)
# ('x', 'y', 'width', 'height', 'angle', 'dilate')
bfPlot.rect(-0.38, 0.0, 0.2, 0.5,alpha=1.,color='gray',fill_alpha=.8,line_width=5,line_color="#1e3246")
bfPlot.rect(-.3, 0.0, 0.6, 0.6,alpha=1.,color='#d2d6da',fill_alpha=0,line_width=1)#line_color="#213447")
bfPlot.toolbar.logo=None
bfImage = bfPlot.image(image='bfdata', x='x', y='y', dw='dw', dh='dh',alpha=0.9,
             color_mapper=colorMapper,source=bv.cdsource)
bfPlot.add_layout(ColorBar(color_mapper=colorMapper,location=(0,0),
                           title="dB",
                           title_standoff=10),'right')
bftooltips = [
    ("L_p (dB)", "@bfdata"),
]
hover = HoverTool(tooltips=bftooltips, mode="mouse",
                    renderers=[bfImage]) # only use hover tool for image renderer
bfPlot.add_tools(hover)


# FrequencySignalPlot
# freqdata = ColumnDataSource(data={'freqs':[],
#                                   'amp':[],
#                                   'colors':[]})
f_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
freqdata = ColumnDataSource(data={'freqs':[array(f_ticks)], # initialize
                                  'amp':[array([0]*len(f_ticks))],
                                  'colors':['white']})
f_ticks_override = {20: '0.02', 50: '0.05', 100: '0.1', 200: '0.2', 
                    500: '0.5', 1000: '1', 2000: '2', 5000: '5', 10000: '10', 
                    20000: '20'}
freqplot = figure(title="Sector-Integrated Spectrum", plot_width=bfplotwidth, plot_height=700,
                  x_axis_type="log", x_axis_label="f / kHz", 
                  y_axis_label="SPL / dB", )#tooltips=TOOLTIPS)
freqplot.toolbar.logo=None
freqplot.xaxis.axis_label_text_font_style = "normal"
freqplot.yaxis.axis_label_text_font_style = "normal"
freqplot.xgrid.minor_grid_line_color = 'navy'
freqplot.xgrid.minor_grid_line_alpha = 0.05
freqplot.xaxis.ticker = f_ticks
freqplot.x_range=Range1d(20, 20000)
freqplot.xaxis.major_label_overrides = f_ticks_override
frLine = freqplot.multi_line('freqs', 'amp',color='colors',alpha=0.0,line_width=3, source=freqdata)

#%% Property Tabs
selectedBfWidgets = column(*bbWidgets.values(),height=1000)  

# create Select Button to select Beamforming Algorithm
settingSelector = Select(title="Select Setting",
                        options=list(settings_dict.keys()),
                        value=list(settings_dict.keys())[0],
                        height=75)

selectedSettingCol = column(list(settings_dict["Time Data"].values()),
                            height=1000)

def select_setting_handler(attr, old, new):
    """changes column layout (changes displayed widgets) 
    according to selected Acoular object
    """
    #print(attr,old,new)
    if not new == "Beamforming Method":
        selectedSettingCol.children = list(settings_dict[new].values())
    else:
        selectedSettingCol.children = selectedBfWidgets.children      
settingSelector.on_change("value",select_setting_handler)

def beamformer_handler(attr,old,new):
    bv.source = beamformer_dict.get(new)[0]
    # if dropdown.value == "bbWidgets"
    selectedBfWidgets.children = list(beamformer_dict.get(new)[1].values())
    if settingSelector.value == "Beamforming Method":
        selectedSettingCol.children = selectedBfWidgets.children 
    #print(selectedBfWidgets.children)
beamformerSelector.on_change('value',beamformer_handler)

#%% Integration sector

sectordata = ColumnDataSource(data={'x':[],'y':[],'width':[], 'height':[]})

def integrate_result(attr,old,new):
    numsectors = len(sectordata.data['x']) 
    if numsectors > 0:
        frLine.glyph.line_alpha=0.8 
        famp = []
        ffreq = []
        colors = []
        for i in range(numsectors):
            sector = array([
                sectordata.data['x'][i]-sectordata.data['width'][i]/2, 
                sectordata.data['y'][i]-sectordata.data['height'][i]/2, 
                sectordata.data['x'][i]+sectordata.data['width'][i]/2, 
                sectordata.data['y'][i]+sectordata.data['height'][i]/2
                ])
            print(sector)
            specamp = acoular.L_p(bv.source.integrate(sector))
            specamp[specamp<-300] = nan
            famp.append(specamp)
            ffreq.append(ps.fftfreq())
            colors.append(COLORS[i])
        freqdata.data.update(amp=famp, freqs=ffreq, colors=colors)
    else:
        frLine.glyph.line_alpha=0.0 # make transparent if no integration sector exist
        freqdata.data = {'freqs':[array(f_ticks)],
                        'amp':[array([0]*len(f_ticks))],
                        'colors':['white']}

   
isector = bfPlot.rect('x', 'y', 'width', 'height',alpha=1.,fill_alpha=0.2,color='black',
                      line_width=3,source=sectordata)
tool = BoxEditTool(renderers=[isector],num_objects=len(COLORS)) # allow only as many boxes as Colors
bfPlot.add_tools(tool)
sectordata.on_change('data',integrate_result)
bv.cdsource.on_change('data',integrate_result) # also change integration result when source map changes

#%% Instructions


instruction_calculation = Div(text="""<p><b>Calculate Source Map:</b></p> <b>Select a desired beamforming method</b> via the "Beamforming Method" widget and <b>press the Calculate Button</b>.
Depending on the method, this may take some time. You may also want to change the desired frequency and bandwith of interest with the "freq" and "num" Textfield widget.
""")

instruction_sector_integration = Div(text="""<p><b>Integrate over Source Map Region:</b></p> <b>Select the "Box Edit Tool"</b> in the upper right corner of the source map figure after calculating the source map.
<b>Hold down the shift key to draw an integration sector</b> in the Source Map. A sector-integrated spectrum should appear. One can <b>remove the sector by pressing the Backspace key</b>.
""")


#%% Document layout

vspace = Div(text='',width=10, height=1000) # just for vertical spacing
vspace2 = Div(text='',width=50, height=20) # just for vertical spacing
hspace = Div(text='',width=100, height=20) # just for horizontal spacing

midlayout = layout([ 
         [Div(text='',width=80, height=10),calcButton,beamformerSelector],
         ])

calcRow = column(
    midlayout,
    freqplot,
    )

settingsCol = column(settingSelector,vspace2,selectedSettingCol,sizing_mode='scale_width')

instructionsCol = column(instruction_calculation, instruction_sector_integration)

leftlayout=layout([ 
        [ Div(text='',width=100, height=0),*bvWidgets.values(),dynamicSlider],
        [bfPlot],
        ])

layout = row(leftlayout,vspace,calcRow,Spacer(width=20),settingsCol,Spacer(width=40),instructionsCol)

# make Document
def server_doc(doc):
    doc.add_root(layout)
    doc.title = "FreqBeamformingExample"

if __name__ == '__main__':
    server = Server({'/': server_doc})
    server.start()
    print('Opening application on http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
else:
    doc = curdoc()
    server_doc(doc)

