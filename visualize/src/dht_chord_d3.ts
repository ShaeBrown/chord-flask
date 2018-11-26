import * as d3 from 'd3';

export class DHTChord {
    public ref: SVGSVGElement;
    private peers: number[];
    private m: number;
    private svg!: d3.Selection<any, any, any, any>;
    private width: number;
    private height: number;
    private cx: number;
    private cy: number;
    private r: number;
    private ticks: number;

    constructor(ref: SVGSVGElement, width: number, height: number, m: number, peers: number[]) {
        this.ref = ref
        this.m = m;
        this.peers = peers
        this.width = width
        this.height = height
        this.cx = this.width / 2
        this.cy = this.height / 2
        this.r = this.width / 2 - 50
        this.ticks = Math.pow(2, this.m)
    }

    draw_key_path(key: number, path: number[]) {
        var lineGenerator = d3.line()
            .curve(d3.curveCardinal);

        for (var i = 1; i < path.length; i++) {
            var coords: [number, number][] = []
            var mid, offset: number
            [mid, offset] = this.get_curve_point(path[i-1], path[i])
            coords[0] = [this.get_x(path[i-1]), this.get_y(path[i-1])]
            coords[1] = [this.get_x(mid, offset), this.get_y(mid, offset)]
            coords[2] = [this.get_x(path[i]), this.get_y(path[i])]
            var pathData: string = lineGenerator(coords) as string;
            this.svg.append('path')
                .attr('d', pathData)
                .attr('stroke-width', 1)
                .attr('fill', 'none')
                .attr('stroke', 'grey');
        }
    }

    get_curve_point(i: number, j: number): [number, number] {
        var left = (i + j)/ 2
        var right = (i + j + this.ticks)/2 % this.ticks
        var left_diff = Math.abs(left - i) % this.ticks
        var right_diff = Math.abs(right - i) % this.ticks
        var linearScale = d3.scaleLog()
                        .domain([0.5, this.ticks/2])
                        .range([25, this.r]);
        
        return left_diff < right_diff ? 
            [left, -linearScale(left_diff)] : 
            [right, -linearScale(right_diff)]
    }

    get_x(i: number, offset: number = 0) {
        return this.cx + (this.r + offset) * Math.sin((i / this.ticks) * Math.PI*2);
    }

    get_y(i: number, offset: number = 0) {
        return this.cy + -(this.r + offset) * Math.cos((i / this.ticks) * Math.PI*2);
    }

    build_chord() {
        this.svg = d3.select(this.ref)
            .attr("font-size", 10)
            .attr("font-family", "sans-serif");
        
        this.svg.append("circle")
            .attr("cx", this.cx)
            .attr("cy", this.cy)
            .attr("r", this.r)
            .style("stroke", "black")
            .style("fill", "none")
            .style("stroke-width", 2);

        var nodes = this.svg.append("g")
            .selectAll("circles")
            .data(this.peers)
            .enter();
        
        nodes.append("circle")
            .attr("cx", (d: any) => { 
                return this.get_x(d)
            })
            .attr("cy", (d: any) => { 
                return this.get_y(d)
            })
           .attr("r", 2);


        nodes.append("text")
            .attr("x", (d: any) => { 
                return this.get_x(d, 10)
            })
            .attr("y", (d: any) => { 
                return this.get_y(d, 10)
            })
            .text((d) => {
                // Check text output under 6 digits
                if (this.ticks > Math.pow(2,20)) {
                    return d3.format(".2e")(d)
                }
                return d
            });
    }
}