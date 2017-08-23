/* MySSD Reader
 * myxxxsquared https://github.com/myxxxsquared/myssd-python
 * GPLv3 License
*/

$(document).ready(function(){
    $.ctx = $("#maincanvas")
    $.myChart = new Chart($.ctx, {})
    $.updateChart = function(chartdata) {
        $.myChart.destroy();
        $.myChart = new Chart($.ctx, chartdata);
    };
    
    $.reloadChart = function() {
        $.get(
            "/data",
            {datafrom: $("input[name='datafrom']:checked").val()}, 
            function(data) {
                $.updateChart(data);
            }
        );
    };
    
    $("#reload, input[type=radio]").click($.reloadChart);
    $("#shutdown").click(function(){
        $.post("/shutdown", function(){
            window.location = 'about:blank';
        });
    });

    $.reloadChart();
});

