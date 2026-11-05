const width = 800;
const height = 550;

const svg = d3.select("#map-container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

// Set Albers USA projection centered directly on California
const projection = d3.geoAlbers()
  .rotate([119.5, 0])
  .center([0, 37.5])
  .scale(3200)
  .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// 1. Load TopoJSON State Boundaries
d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json").then(us => {
  const states = topojson.feature(us, us.objects.states);

  // Render state boundaries
  svg.selectAll("path")
    .data(states.features)
    .enter()
    .append("path")
    .attr("class", "state-boundary")
    .attr("d", path);

  // 2. Load Sample Fire Data from JSON
  d3.json("data/fire_sample.json").then(fireData => {
    svg.selectAll("circle")
      .data(fireData)
      .enter()
      .append("circle")
      .attr("class", "fire-node")
      .attr("cx", d => {
        // Use coordinates if available, or project fallback grid
        if (d.lon && d.lat) return projection([d.lon, d.lat])[0];
        return 300 + (Math.random() * 200);
      })
      .attr("cy", d => {
        if (d.lon && d.lat) return projection([d.lon, d.lat])[1];
        return 150 + (Math.random() * 250);
      })
      .attr("r", d => {
        // Size circle based on Fire Radiative Power (MW)
        const frp = d.FRP || 20;
        return Math.max(3, Math.min(15, Math.sqrt(frp)));
      });
  }).catch(err => {
    console.warn("Could not load data/fire_sample.json, rendering placeholder map.", err);
  });
});