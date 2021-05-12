// window.onload = function() {
//     time_series = [];
//     fetch('/logs/manifest.json')
//     .then(response => response.text())
//     .then((data) => {
//         manifest = JSON.parse(data);
//         value = manifest[Object.keys(manifest)[0]];

//         fetch('/logs/' + value['data'])
//         .then(response => response.text())
//         .then((data) => {
//             // parse rudimentary csv
//             lines = data.split('\n');
//             unixtime = 0;
//             last_unixtime = 0;
//             lines.forEach(line => {
//                 cells = line.split(',');
//                 if (cells.length <= 1) {
//                     return;
//                 }
//                 for (i = 0; i < cells.length-1; i++) {
//                     if (time_series[i] == null) {
//                         time_series[i] = [];
//                     }
//                     if (i == 0) {
//                         last_unixtime = unixtime;
//                         timestamp = cells[i];
//                         year = parseInt(timestamp.substring(0, 4));
//                         month = parseInt(timestamp.substring(5,7));
//                         day = parseInt(timestamp.substring(8, 10));
//                         hour = parseInt(timestamp.substring(11, 13));
//                         minute = parseInt(timestamp.substring(13, 15));
//                         second = parseInt(timestamp.substring(15, 18));
//                         date = new Date(year, month, day, hour, minute, second);
//                         unixtime = date.getTime() / 1000;  // milliseconds to seconds
//                         // note time zone is not correct here, expects UTC time but is provided local time.
//                         time_series[i].push(unixtime);
//                     } else {
//                         time_delta = unixtime - last_unixtime;
//                         num_bytes = parseInt(cells[i]);
//                         bytes_per_second = num_bytes / time_delta;
//                         time_series[i].push(bytes_per_second / 1000);
//                     }
//                 }
//             });

//             for (i = 0; i < time_series.length; i++) {
//                 opts.series.push({
//                     show: true,
//                     stroke: "red",
//                     width: 1,
//                     fill: "rgba(255, 0, 0, 0.3)",
//                 });
//             }

//             let uplot = new uPlot(opts, time_series, document.body);
//         });
//     });
// }