// Load real GOES-18 satellite data
d3.json("data/combined.json").then(data => {

  data.forEach(d => {
    d.date = new Date(d.timestamp);
    d.total_frp = +d.total_frp;
    d.water_vapor_bt = d.water_vapor_bt == null
      ? null : +d.water_vapor_bt;
  });

  data.sort((a, b) => a.date - b.date);

  // Graph dimensions
  const width = 800;
  const height = 400;
  const margin = {top: 30, right: 70, bottom: 55, left: 70};

  const svg = d3.select("#comparison-chart")
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .style("width", "100%")
    .style("max-width", "1100px");

  // X-axis: Time
  const x = d3.scaleUtc()
    .domain(d3.extent(data, d => d.date))
    .range([margin.left, width - margin.right]);

  // Left Y-axis: Water vapor brightness temperature
  const yMoisture = d3.scaleLinear()
    .domain(d3.extent(
      data.filter(d => d.water_vapor_bt != null),
      d => d.water_vapor_bt
    ))
    .nice()
    .range([height - margin.bottom, margin.top]);

  // Right Y-axis: Fire radiative power
  const yFire = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.total_frp) || 1])
    .nice()
    .range([height - margin.bottom, margin.top]);

  // Draw axes
  svg.append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(6)
      .tickFormat(d3.utcFormat("%b %d")));

  svg.append("g")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(yMoisture));

  svg.append("g")
    .attr("transform", `translate(${width - margin.right},0)`)
    .call(d3.axisRight(yFire));

  // Moisture line (BLUE)
  const moistureLine = d3.line()
    .defined(d => d.water_vapor_bt != null)
    .x(d => x(d.date))
    .y(d => yMoisture(d.water_vapor_bt));

  svg.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "#00d4ff")
    .attr("stroke-width", 2.5)
    .attr("d", moistureLine);

  // Fire line (ORANGE)
  const fireLine = d3.line()
    .x(d => x(d.date))
    .y(d => yFire(d.total_frp));

  svg.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "#ff6b35")
    .attr("stroke-width", 2.5)
    .attr("d", fireLine);

// Vertical line showing the selected hour
const selectedTimeLine = svg.append("line")
  .attr("y1", margin.top)
  .attr("y2", height - margin.bottom)
  .attr("stroke", "#ffffff")
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "5,5")
  .attr("opacity", 0.8);

// Update marker whenever the map slider moves
window.addEventListener("fireTimeChange", event => {

  const selectedDate = new Date(event.detail.timestamp);
  const position = x(selectedDate);

  selectedTimeLine
    .attr("x1", position)
    .attr("x2", position);
});

  // Labels
  svg.append("text")
    .attr("x", margin.left)
    .attr("y", 17)
    .attr("fill", "#00d4ff")
    .attr("font-size", 13)
    .text("Atmospheric temperature reading (K)");

  svg.append("text")
    .attr("x", width - margin.right)
    .attr("y", 17)
    .attr("text-anchor", "end")
    .attr("fill", "#ff6b35")
    .attr("font-size", 13)
    .text("Fire intensity (radiated power, MW)");

  // Hover tooltip
  const tooltip = d3.select("#comparison-chart")
    .append("div")
    .style("position", "absolute")
    .style("background", "#252525")
    .style("color", "white")
    .style("padding", "10px")
    .style("border-radius", "6px")
    .style("pointer-events", "none")
    .style("display", "none");

  d3.select("#comparison-chart")
    .style("position", "relative");

  svg.append("rect")
    .attr("x", margin.left)
    .attr("y", margin.top)
    .attr("width", width - margin.left - margin.right)
    .attr("height", height - margin.top - margin.bottom)
    .attr("fill", "transparent")
    .on("mousemove", function(event) {

      const [mx] = d3.pointer(event, this);

      const hoveredDate = x.invert(mx + margin.left);

      const closest = d3.least(
        data,
        d => Math.abs(d.date - hoveredDate)
      );

      if (!closest) return;

      const localTime = closest.date.toLocaleString("en-US", {
        timeZone: "America/Los_Angeles",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit"
      });

      tooltip
        .style("display", "block")
        .style("left", `${event.offsetX + 15}px`)
        .style("top", `${event.offsetY + 15}px`)
        .html(`
          <strong>${localTime} PDT</strong><br>
          🔥 FRP: ${closest.total_frp.toFixed(1)} MW<br>
          💧 Brightness temp:
          ${closest.water_vapor_bt == null
            ? "N/A"
            : closest.water_vapor_bt.toFixed(1) + " K"}
        `);
    })
    .on("mouseleave", () => {
      tooltip.style("display", "none");
    });

}).catch(error => {
  console.error("Failed to load combined data:", error);
});