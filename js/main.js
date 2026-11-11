const width = 800;
const height = 550;

const svg = d3.select("#map-container")
  .append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`);

// Everything inside this group will zoom together
const mapGroup = svg.append("g");

const zoom = d3.zoom()
    .scaleExtent([1, 12])
    .on("zoom", event => {
        mapGroup.attr("transform", event.transform);
    });

svg.call(zoom);

const projection = d3.geoMercator()
    .center([-119.5, 37])
    .scale(1900)
    .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// Create map
d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json")
  .then(async us => {

    const states = topojson.feature(us, us.objects.states);

    // Find California
const california = states.features.find(
    d => String(d.id).padStart(2, "0") === "06"
);

// Fit the entire state inside the map
projection.fitExtent(
    [[70, 40], [width - 70, height - 40]],
    california
);

  // California-shaped clipping boundary
svg.append("defs")
    .append("clipPath")
    .attr("id", "california-clip")
    .append("path")
    .attr("d", path(california));

    mapGroup.selectAll(".state-boundary")
      .data(states.features)
      .enter()
      .append("path")
      .attr("class", "state-boundary")
      .attr("d", path);

    // Create a soft fade around the Park Fire region
const center = projection([-121.76, 39.79]);

const defs = svg.append("defs");

const gradient = defs.append("radialGradient")
    .attr("id", "moisture-fade");

gradient.append("stop")
    .attr("offset", "0%")
    .attr("stop-color", "white");

gradient.append("stop")
    .attr("offset", "65%")
    .attr("stop-color", "white");

gradient.append("stop")
    .attr("offset", "100%")
    .attr("stop-color", "black");

const mask = defs.append("mask")
    .attr("id", "moisture-mask");

mask.append("circle")
    .attr("cx", center[0])
    .attr("cy", center[1])
    .attr("r", 220)
    .attr("fill", "url(#moisture-fade)");

    // Separate SVG layers
    const moistureLayer = mapGroup.append("g")
    .attr("clip-path", "url(#california-clip)");
    const fireLayer = mapGroup.append("g")
    .attr("clip-path", "url(#california-clip)");

    // Park Fire marker
const parkLocation = projection([-121.76, 39.79]);

const parkMarker = mapGroup.append("g")
    .attr("class", "park-marker")
    .attr("transform", `translate(${parkLocation[0]}, ${parkLocation[1]})`)
    .style("cursor", "pointer");

// Outer glow
parkMarker.append("circle")
    .attr("r", 16)
    .attr("fill", "#ff5722")
    .attr("opacity", 0.2);

// Main marker
parkMarker.append("circle")
    .attr("r", 8)
    .attr("fill", "#ff5722")
    .attr("stroke", "white")
    .attr("stroke-width", 2);

// Label
parkMarker.append("text")
    .attr("x", 14)
    .attr("y", 5)
    .attr("fill", "white")
    .attr("font-size", 12)
    .attr("font-weight", "bold")
    .text("Park Fire");

// Open detailed graph when clicked
parkMarker.on("click", event => {
    event.stopPropagation();

    d3.select("#fire-popup")
        .style("display", "flex");
});

  const [moistureFrames, data, californiaFire] = await Promise.all([
      d3.json("data/moisture_frames.json"),
      d3.json("data/combined.json"),
      d3.json("data/california_fire.json")
  ]);

    data.sort((a, b) =>
      new Date(a.timestamp) - new Date(b.timestamp)
    );

  // Look up California-wide fire detections by hour
const californiaFiresByHour = new Map(
    californiaFire.map(d => [
        d.timestamp.slice(0, 13),
        d.fires
    ])
);

// Water-vapor brightness temperature colors
const moistureColor = d3.scaleSequential()
    .domain([250, 230])
    .interpolator(d3.interpolateBlues);
// Smooth atmospheric contours (D3 only)
const contourGenerator = d3.contours()
    .size([moistureFrames.cols, moistureFrames.rows])
    .thresholds(d3.range(226, 253, 3))
    .smooth(true);

// Convert contour grid coordinates to map coordinates
function contourPath(contour) {
    let result = "";

    for (const polygon of contour.coordinates) {
        for (const ring of polygon) {

            ring.forEach(([x, y], i) => {
                const lon =
                    moistureFrames.longitudes[0] +
                    (x - 0.5) * moistureFrames.step;

                const lat =
                    moistureFrames.latitudes[0] +
                    (y - 0.5) * moistureFrames.step;

                const point = projection([lon, lat]);

                if (point) {
                    result +=
                        `${i === 0 ? "M" : "L"}${point[0]},${point[1]}`;
                }
            });

            result += "Z";
        }
    }

    return result;
}
// Draw California outline over the blue moisture layer
mapGroup.append("path")
    .datum(california)
    .attr("d", path)
    .attr("fill", "none")
    .attr("stroke", "#dddddd")
    .attr("stroke-width", 1.5)
    .style("pointer-events", "none");

    // Water-vapor brightness temperature legend
const legend = svg.append("g")
    .attr("transform", "translate(25, 470)");

legend.append("text")
    .attr("fill", "white")
    .attr("font-size", 12)
    .text("Atmospheric Conditions (Satellite Temperature, K)");

    legend.append("text")
    .attr("x", 0)
    .attr("y", 55)
    .attr("fill", "#bbbbbb")
    .attr("font-size", 10)
    .text("Blue shows atmospheric water-vapor satellite measurements.");

const legendScale = d3.scaleLinear()
    .domain([230, 250])
    .range([0, 200]);

legend.selectAll("rect")
    .data(d3.range(230, 250, 0.25))
    .join("rect")
    .attr("x", d => legendScale(d))
    .attr("y", 12)
    .attr("width", 3)
    .attr("height", 12)
    .attr("fill", d => moistureColor(d));

legend.append("g")
    .attr("transform", "translate(0, 24)")
    .call(d3.axisBottom(legendScale).ticks(5))
    .selectAll("text")
    .attr("fill", "white");


    // Slider controls
    const slider = d3.select("#time-slider")
      .attr("max", data.length - 1);

    const label = d3.select("#time-label");

    const framesByHour = new Map(
    moistureFrames.frames.map(f => [
        f.timestamp.slice(0, 13),
        f
    ])
);

    function updateMap(index) {

      const observation = data[index];
      if (!observation) return;

            // Match the fire observation to the corresponding moisture hour
      const hourKey = observation.timestamp.slice(0, 13);

      const frame = framesByHour.get(hourKey);

     
// Update smooth temperature contours
if (frame) {

    const values = frame.values.map(v =>
        v === null ? -999 : v / 10
    );

    const contours = contourGenerator(values);

    moistureLayer.selectAll(".temperature-contour")
        .data(contours, d => d.value)
        .join("path")
        .attr("class", "temperature-contour")
        .attr("d", contourPath)
        .attr("fill", d => moistureColor(d.value))
        .attr("fill-rule", "evenodd")
        .attr("stroke", "none")
        .attr("opacity", 0.75)
        .style("pointer-events", "none");

} else {
    moistureLayer.selectAll(".temperature-contour").remove();
}
      const fires = californiaFiresByHour.get(hourKey) || [];

      // Update fire circles for selected hour
      fireLayer.selectAll(".fire-node")
        .data(fires, (d, i) => i)
        .join(
          enter => enter.append("circle")
            .attr("class", "fire-node")
            .attr("r", 0),

          update => update,

          exit => exit.remove()
        )
        .attr("cx", d => projection([d.lon, d.lat])[0])
        .attr("cy", d => projection([d.lon, d.lat])[1])
        .attr("r", d => Math.max(2, Math.min(9, Math.sqrt(d.FRP) * 0.6)))

      // Date and time in California
      const date = new Date(observation.timestamp);

      const formatted = date.toLocaleString("en-US", {
        timeZone: "America/Los_Angeles",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short"
      });

      label.text(
        `${formatted} | ${fires.length} detected fire pixels`
      );

      // Notify comparison chart of selected time
      window.dispatchEvent(new CustomEvent("fireTimeChange", {
        detail: { timestamp: observation.timestamp }
      }));
    }

    slider.on("input", function() {
      updateMap(+this.value);
    });

    // Play/pause animation
    let timer = null;

    d3.select("#play-button").on("click", function() {

      if (timer) {
        clearInterval(timer);
        timer = null;
        d3.select(this).text("▶ Play");
        return;
      }

      d3.select(this).text("⏸ Pause");

      timer = setInterval(() => {
        let next = +slider.property("value") + 1;

        if (next >= data.length) next = 0;

        slider.property("value", next);
        updateMap(next);

      }, 400);
    });

    // Show first hour
    updateMap(0);

  })
  .catch(error => console.error(error));


  d3.select("#close-popup").on("click", () => {
    d3.select("#fire-popup")
        .style("display", "none");
});