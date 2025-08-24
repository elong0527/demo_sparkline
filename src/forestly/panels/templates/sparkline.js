function(${function_params}) {
  // Create Plotly component
  const PlotComponent = window.createPlotlyComponent ? window.createPlotlyComponent(window.Plotly) : 
    class extends React.Component {
      componentDidMount() {
        window.Plotly.newPlot(this.el, this.props.data, this.props.layout, this.props.config);
      }
      componentWillUnmount() {
        window.Plotly.purge(this.el);
      }
      render() {
        return React.createElement('div', {ref: (el) => this.el = el});
      }
    };
  
  // Parse configuration
  const config = ${sparkline_config};
  
  // Generate data traces
  const traces = [];
  
  config.variables.forEach((variable, i) => {
    const value = cell.row[variable];
    if (value != null && value !== undefined) {
      const trace = {
        x: [value],
        y: [i * 0.15],
        type: 'scatter',
        mode: 'markers',
        marker: {size: 8, color: config.colors[i]},
        name: config.labels[i],
        hovertemplate: config.labels[i] + ': %{x}<extra></extra>'
      };
      
      // Add error bars if bounds are provided
      if (config.lower[i] && config.upper[i]) {
        const lower = cell.row[config.lower[i]];
        const upper = cell.row[config.upper[i]];
        if (lower != null && upper != null) {
          trace.error_x = {
            type: 'data',
            symmetric: false,
            array: [upper - value],
            arrayminus: [value - lower],
            visible: true,
            color: config.colors[i],
            thickness: 1.5,
            width: 3
          };
        }
      }
      
      traces.push(trace);
    }
  });
  
  if (traces.length === 0) return null;
  const yRange = traces.length > 1 ? [-0.2, (traces.length - 1) * 0.15 + 0.2] : [-0.5, 0.5];
  
  // Handle x-axis limits
  let xlim = null;
  if (config.xlim) {
    const xPadding = (config.xlim[1] - config.xlim[0]) * 0.02;
    xlim = [config.xlim[0] - xPadding, config.xlim[1] + xPadding];
  }
  
  // Handle reference line
  const shapes = [];
  if (config.reference_line !== null) {
    const refValue = typeof config.reference_line === 'string' 
      ? cell.row[config.reference_line] 
      : config.reference_line;
    
    if (refValue != null) {
      shapes.push({
        type: 'line',
        x0: refValue,
        x1: refValue,
        y0: yRange[0],
        y1: yRange[1],
        line: {color: config.reference_line_color || '#999999', width: 1, dash: 'dash'}
      });
    }
  }
  
  // Layout configuration
  const layout = {
    height: config.height || 45,
    width: config.width || 300,
    margin: {l: 10, r: 10, t: 5, b: 5},
    xaxis: {
      range: xlim,
      zeroline: false,
      showticklabels: false,
      showgrid: false,
      fixedrange: true,
      title: null
    },
    yaxis: {
      visible: false,
      range: yRange,
      fixedrange: true
    },
    showlegend: false,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    shapes: shapes,
    annotations: []
  };
  
  return React.createElement(PlotComponent, {
    data: traces,
    layout: layout,
    config: {displayModeBar: false, responsive: true}
  });
}
