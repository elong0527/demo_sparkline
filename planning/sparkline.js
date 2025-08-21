function(cell, state) {
  // Ensure createPlotlyComponent is available
  const Plot = typeof createPlotlyComponent !== 'undefined' 
    ? createPlotlyComponent(Plotly)
    : class extends React.Component {
        componentDidMount() {
          Plotly.newPlot(this.el, this.props.data, this.props.layout, this.props.config);
        }
        componentDidUpdate() {
          Plotly.react(this.el, this.props.data, this.props.layout, this.props.config);
        }
        render() {
          return React.createElement('div', {ref: (el) => this.el = el});
        }
      };
  
  // Data variables
  const x = [${js_x}];
  const y = [${js_y}];
  const x_lower = [${js_x_lower}];
  const x_upper = [${js_x_upper}];
  const text = [${js_text}];
  const color = [${js_color}];
  const color_errorbar = [${js_color_errorbar}];
  
  // Layout variables
  const x_range = [${js_x_range}];
  const y_range = [${js_y_range}];
  const vline = ${js_vline};
  const height = ${js_height};
  const width = ${js_width};
  const color_vline = ${js_color_vline};
  const margin = [${js_margin}];
  const x_label = "${js_xlab}";
  
  // Legend variables
  const showlegend = ${js_showlegend};
  const legend_title = "${js_legend_title}";
  const legend_position = ${js_legend_position};
  const legend_label = [${js_legend_label}];

  return React.createElement(Plot, {
    data: [
      ${data_trace}
    ],
    layout: {
      height: height,
      width: width,
      margin: {
        b: margin[0],
        l: margin[1],
        t: margin[2],
        r: margin[3],
        pad: margin[4]
      },
      xaxis: {
        domain: [0, 1],
        title: {
          text: x_label,
          standoff: 0,
          font: { size: 12 }
        },
        range: x_range,
        showline: true,
        ticks: "outside",
        zeroline: false,
        fixedrange: true
      },
      yaxis: {
        domain: [0, 1],
        title: "",
        range: y_range,
        showgrid: false,
        zeroline: false,
        showticklabels: false,
        fixedrange: true
      },
      shapes: vline !== null && vline !== "[]" ? [{
        type: "line",
        y0: y_range[0],
        y1: y_range[1],
        yref: "paper",
        x0: vline,
        x1: vline,
        line: { color: color_vline }
      }] : [],
      plot_bgcolor: "rgba(0, 0, 0, 0)",
      paper_bgcolor: "rgba(0, 0, 0, 0)",
      hoverlabel: { bgcolor: "lightgray" },
      showlegend: showlegend,
      hovermode: "closest",
      legend: {
        title: { text: legend_title },
        orientation: "h",
        xanchor: "center",
        x: 0.5,
        y: legend_position
      }
    },
    config: {
      showSendToCloud: false,
      displayModeBar: false
    }
  });
}