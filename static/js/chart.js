// Track if component is mounted
let isMounted = false;
let currentChart = null;

function showChartError(msg) {
    if (!isMounted) return;
    const errorElement = document.getElementById('chart-error');
    const loadingElement = document.getElementById('chart-loading');
    const chartElement = document.getElementById('stockChartApex');
    
    if (errorElement) errorElement.innerText = msg;
    if (errorElement) errorElement.style.display = 'block';
    if (loadingElement) loadingElement.style.display = 'none';
    if (chartElement) chartElement.innerHTML = '';
}

function cleanupChart() {
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
}

function renderApexChart(dates, prices, symbol, buyTransactions, sellTransactions, splitEvents) {
    if (!isMounted) return;
    
    // Cleanup any existing chart
    cleanupChart();
    
    // Validate input data
    if (!dates || !prices || dates.length === 0 || prices.length === 0) {
        showChartError('No chart data available');
        return;
    }
    
    if (dates.length !== prices.length) {
        console.error('Data mismatch:', { dates: dates.length, prices: prices.length });
        showChartError('Invalid chart data');
        return;
    }
    
    // Convert data to chart format
    const chartData = dates.map((date, index) => ({
        x: new Date(date).getTime(),
        y: prices[index]
    })).filter(point => !isNaN(point.y));
    
    if (chartData.length === 0) {
        showChartError('No valid price data available');
        return;
    }
    
    // Create the series data
    var seriesData = [{
        name: symbol + ' Price',
        type: 'line',
        data: chartData
    }];
    
    // Process buy transactions
    if (buyTransactions && buyTransactions.length > 0) {
        const buyData = buyTransactions
            .map(tx => {
                try {
                    return {
                        x: new Date(tx.date + ' ' + (tx.time || '00:00:00')).getTime(),
                        y: parseFloat(tx.price),
                        transaction_id: tx.id,
                        qty: tx.qty,
                        date: tx.date,
                        time: tx.time,
                        fillColor: '#2ecc71'
                    };
                } catch (e) {
                    console.error('Error processing buy transaction:', e, tx);
                    return null;
                }
            })
            .filter(point => point !== null && !isNaN(point.y));
        
        if (buyData.length > 0) {
            seriesData.push({
                name: 'Buy Orders',
                type: 'scatter',
                data: buyData
            });
        }
    }
    
    // Process sell transactions
    if (sellTransactions && sellTransactions.length > 0) {
        const sellData = sellTransactions
            .map(tx => {
                try {
                    return {
                        x: new Date(tx.date + ' ' + (tx.time || '00:00:00')).getTime(),
                        y: parseFloat(tx.price),
                        transaction_id: tx.id,
                        qty: tx.qty,
                        date: tx.date,
                        time: tx.time,
                        fillColor: '#e74c3c'
                    };
                } catch (e) {
                    console.error('Error processing sell transaction:', e, tx);
                    return null;
                }
            })
            .filter(point => point !== null && !isNaN(point.y));
        
        if (sellData.length > 0) {
            seriesData.push({
                name: 'Sell Orders',
                type: 'scatter',
                data: sellData
            });
        }
    }
    
    // Process split events
    let annotations = {
        xaxis: [],
        points: []
    };
    
    if (splitEvents && splitEvents.length > 0) {
        splitEvents.forEach(split => {
            if (split.date && split.ratio) {
                // Add vertical line annotation
                annotations.xaxis.push({
                    x: new Date(split.date).getTime(),
                    borderColor: '#4f8cff',
                    strokeDashArray: 5,
                    label: {
                        borderColor: '#4f8cff',
                        style: {
                            color: '#fff',
                            background: '#4f8cff',
                            fontSize: '12px',
                            padding: {
                                left: 8,
                                right: 8,
                                top: 4,
                                bottom: 4
                            }
                        },
                        text: `${split.ratio}:1 Split`,
                        orientation: 'horizontal',
                        offsetY: 20
                    }
                });
                
                // Add point annotation if we have a price
                if (split.price) {
                    annotations.points.push({
                        x: new Date(split.date).getTime(),
                        y: split.price,
                        marker: {
                            size: 8,
                            fillColor: '#4f8cff',
                            strokeColor: '#fff',
                            strokeWidth: 2
                        },
                        label: {
                            borderColor: '#4f8cff',
                            style: {
                                color: '#fff',
                                background: '#4f8cff'
                            },
                            text: 'Split Point'
                        }
                    });
                }
            }
        });
    }
    
    // Create chart options
    var options = {
        series: seriesData,
        chart: {
            height: 400,
            type: 'line',
            animations: { enabled: false },
            zoom: { enabled: true },
            toolbar: { show: true }
        },
        stroke: {
            curve: 'straight',
            width: [2, 0, 0]
        },
        markers: {
            size: [0, 8, 8],
            hover: { size: 11 }
        },
        annotations: annotations,
        tooltip: {
            shared: false,
            intersect: true,
            x: { format: 'yyyy-MM-dd' },
            y: { formatter: function(val) { return '$' + val.toFixed(2); } },
            fixed: {
                enabled: true,
                position: 'topLeft',
                offsetX: 90,
                offsetY: 0
            },
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                // Only customize for buy/sell points
                if (seriesIndex === 0) return;
                
                const point = w.config.series[seriesIndex].data[dataPointIndex];
                if (!point || !point.qty) return;
                
                const seriesName = w.config.series[seriesIndex].name;
                const price = point.y.toFixed(2);
                const date = new Date(point.x).toLocaleDateString();
                const time = point.time || 'N/A';
                
                // Determine color based on transaction type
                const bgColor = seriesName.toLowerCase().includes('buy') ? '#e6f7ed' : '#fae9e8';
                const textColor = seriesName.toLowerCase().includes('buy') ? '#2ecc71' : '#e74c3c';
                
                return '<div class="custom-tooltip" style="background-color: ' + bgColor + '; border: 1px solid ' + textColor + '; padding: 8px; border-radius: 4px;">' +
                    '<div class="tooltip-title" style="font-weight: bold; color: ' + textColor + ';">' + seriesName + '</div>' +
                    '<div class="tooltip-date">Date: ' + date + '</div>' +
                    '<div class="tooltip-time">Time: ' + time + '</div>' +
                    '<div class="tooltip-price">Price: $' + price + '</div>' +
                    '<div class="tooltip-qty">Quantity: ' + point.qty + '</div>' +
                    '</div>';
            }
        },
        grid: {
            show: true
        },
        xaxis: {
            type: 'datetime',
            labels: {
                datetimeUTC: false,
                format: 'yyyy-MM-dd'
            }
        },
        yaxis: {
            labels: {
                formatter: function(val) {
                    return '$' + val.toFixed(2);
                }
            },
            tickAmount: 8
        }
    };
    
    try {
        const chartElement = document.querySelector("#stockChartApex");
        if (!chartElement || !isMounted) {
            console.error('Chart element not found or component unmounted');
            return;
        }
        
        currentChart = new ApexCharts(chartElement, options);
        currentChart.render().then(() => {
            if (!isMounted) {
                cleanupChart();
                return;
            }
            const loadingElement = document.getElementById('chart-loading');
            if (loadingElement) loadingElement.style.display = 'none';
        }).catch(e => {
            if (!isMounted) return;
            console.error('Error rendering chart:', e);
            showChartError('Error rendering chart: ' + e.message);
        });
    } catch (e) {
        if (!isMounted) return;
        console.error('Error creating chart:', e);
        showChartError('Error creating chart: ' + e.message);
    }
}

// Initialize chart when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    isMounted = true;
    
    // Load chart data
    const loadChart = () => {
        const currentFilter = document.querySelector('#currentFilter')?.value;
        if (!currentFilter || !isMounted) return;
        
        const selectedRange = new URLSearchParams(window.location.search).get('range') || 'all';
        
        fetch(`/api/stock_chart/${currentFilter}?range=${selectedRange}`)
            .then(resp => {
                if (!isMounted) throw new Error('Component unmounted');
                return resp.json();
            })
            .then(data => {
                if (!isMounted) return;
                
                if (data.error) {
                    showChartError('Price data temporarily unavailable. Please try again in a few minutes.');
                } else if (data.dates && data.dates.length && data.prices && data.prices.length) {
                    renderApexChart(
                        data.dates, 
                        data.prices, 
                        currentFilter,
                        data.buy_transactions || [],
                        data.sell_transactions || [],
                        data.split_events || []
                    );
                } else {
                    showChartError('No chart data available.');
                }
            })
            .catch(error => {
                if (!isMounted) return;
                console.error('Error loading chart:', error);
                showChartError('Error loading chart. Please try again.');
            });
    };
    
    // Load chart with a slight delay to ensure DOM is ready
    requestAnimationFrame(loadChart);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    isMounted = false;
    cleanupChart();
});

// Cleanup on page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        isMounted = false;
        cleanupChart();
    } else {
        isMounted = true;
        requestAnimationFrame(() => {
            const loadingElement = document.getElementById('chart-loading');
            if (loadingElement) loadingElement.style.display = 'block';
            const chartElement = document.getElementById('stockChartApex');
            if (chartElement) chartElement.innerHTML = '';
            loadChart();
        });
    }
});

// Function to highlight transaction row
function highlightTransaction(transactionId) {
    // First, remove any existing highlights
    document.querySelectorAll('tr.highlighted-row').forEach(function(el) {
        el.classList.remove('highlighted-row');
    });
    
    // Find and highlight the row with matching transaction ID
    const row = document.querySelector('tr[data-transaction-id="' + transactionId + '"]');
    if (row) {
        row.classList.add('highlighted-row');
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
} 