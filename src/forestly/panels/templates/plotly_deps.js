// Load all required dependencies for Plotly visualization in the correct order
(function() {
    // Check if all dependencies are already loaded
    if (typeof window.React !== 'undefined' && 
        typeof window.ReactDOM !== 'undefined' && 
        typeof window.Plotly !== 'undefined') {
        console.log('All dependencies already loaded');
        return;
    }
    
    // Save original define to handle RequireJS/AMD environments
    var originalDefine = window.define;
    
    // Temporarily undefine to force libraries to load in global mode
    window.define = undefined;
    
    // Load scripts sequentially to ensure proper order
    function loadScript(src, callback) {
        var script = document.createElement('script');
        script.src = src;
        script.onload = callback;
        script.onerror = function() {
            console.error('Failed to load: ' + src);
        };
        document.head.appendChild(script);
    }
    
    // Function to create Plotly component after all libs are loaded
    function setupPlotlyComponent() {
        // Restore RequireJS define
        if (originalDefine) {
            window.define = originalDefine;
        }
        
        // Create the Plotly React component
        if (typeof window.React !== 'undefined' && typeof window.Plotly !== 'undefined') {
            window.createPlotlyComponent = window.createPlotlyComponent || function(Plotly) {
                return class extends React.Component {
                    componentDidMount() {
                        if (this.el) {
                            Plotly.newPlot(this.el, this.props.data, this.props.layout, this.props.config);
                        }
                    }
                    componentDidUpdate() {
                        if (this.el) {
                            Plotly.react(this.el, this.props.data, this.props.layout, this.props.config);
                        }
                    }
                    componentWillUnmount() {
                        if (this.el) {
                            Plotly.purge(this.el);
                        }
                    }
                    render() {
                        return React.createElement('div', {ref: (el) => this.el = el});
                    }
                };
            };
            console.log('Plotly component setup complete');
        }
    }
    
    // Load libraries in sequence: React -> ReactDOM -> Plotly
    function loadDependencies() {
        // Step 1: Load React
        if (typeof window.React === 'undefined') {
            console.log('Loading React...');
            loadScript('https://unpkg.com/react@17/umd/react.production.min.js', function() {
                console.log('React loaded');
                loadReactDOM();
            });
        } else {
            loadReactDOM();
        }
    }
    
    function loadReactDOM() {
        // Step 2: Load ReactDOM
        if (typeof window.ReactDOM === 'undefined') {
            console.log('Loading ReactDOM...');
            loadScript('https://unpkg.com/react-dom@17/umd/react-dom.production.min.js', function() {
                console.log('ReactDOM loaded');
                loadPlotly();
            });
        } else {
            loadPlotly();
        }
    }
    
    function loadPlotly() {
        // Step 3: Load Plotly
        if (typeof window.Plotly === 'undefined') {
            console.log('Loading Plotly...');
            loadScript('https://unpkg.com/plotly.js@2.18.2/dist/plotly.min.js', function() {
                console.log('Plotly loaded');
                setupPlotlyComponent();
            });
        } else {
            setupPlotlyComponent();
        }
    }
    
    // Start loading sequence
    loadDependencies();
})();