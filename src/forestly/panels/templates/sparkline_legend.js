function() {
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
  
  // Parse legend configuration
  const config = ${legend_config};
  
  // Generate traces for legend markers
  const traces = [];
  const annotations = [];
  
  config.labels.forEach((label, i) => {
    // Add marker trace
    traces.push({
      x: [i * 10],
      y: [0],
      type: 'scatter',
      mode: 'markers',
      marker: {size: 10, color: config.colors[i]},
      name: label,
      showlegend: false
    });
    
    // Add text annotation
    annotations.push({
      x: i * 10 + 1.5,
      y: 0,
      text: label,
      showarrow: false,
      xanchor: 'left',
      yanchor: 'middle',
      font: {size: 11}
    });
  });
  
  // Layout configuration
  const layout = {
    height: config.height || 25,
    width: config.width || 300,
    margin: {l: 5, r: 5, t: 5, b: 5},
    xaxis: {
      range: [-2, config.labels.length * 10],
      zeroline: false,
      showticklabels: false,
      showgrid: false,
      fixedrange: true,
      title: null
    },
    yaxis: {
      visible: false,
      range: [-0.5, 0.5],
      fixedrange: true
    },
    showlegend: false,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    shapes: [],
    annotations: annotations
  };
  
  return React.createElement(PlotComponent, {
    data: traces,
    layout: layout,
    config: {displayModeBar: false, responsive: true}
  });
}