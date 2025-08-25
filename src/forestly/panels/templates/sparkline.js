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
  const font_size = ${js_font_size};

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
          standoff: 5,
          font: { size: font_size }
        },
        range: x_range,
        showline: ${js_show_xaxis},
        showticklabels: ${js_show_xaxis},
        ticks: ${js_show_xaxis} ? "outside" : "",
        tickfont: { size: 10 },
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
        y0: -0.1,
        y1: 1.1,
        yref: "paper",
        x0: vline,
        x1: vline,
        line: { color: color_vline, width: 1 }
      }] : [],
      plot_bgcolor: "rgba(0, 0, 0, 0)",
      paper_bgcolor: "rgba(0, 0, 0, 0)",
      hoverlabel: { bgcolor: "lightgray" },
      showlegend: showlegend,
      hovermode: "closest",
      legend: {
        title: { 
          text: legend_title,
          font: { size: font_size }
        },
        font: { size: font_size },
        orientation: "h",
        xanchor: "center",
        yanchor: "top",  // Anchor from top to align with x-label baseline
        x: 0.5,
        y: legend_position,
        yref: "paper"  // Use paper coordinates for consistent positioning
      }
    },
    config: {
      showSendToCloud: false,
      displayModeBar: false
    }
  });
}