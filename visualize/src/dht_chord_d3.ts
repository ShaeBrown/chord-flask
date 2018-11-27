import * as d3 from 'd3';

export class DHTChord {
    public root: string;
    private peers: number[];
    private m: number;
    private svg!: d3.Selection<any, any, any, any>;
    private width: number;
    private height: number;
    private cx: number;
    private cy: number;
    private r: number;
    private ticks: number;

    constructor(root: string, width: number, height: number, m: number, peers: number[]) {
        this.root = root
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
        var lineGenerator = d3.line().curve(d3.curveCardinal);
        this.svg.append("circle")
            .attr("cx", this.get_x(key))
            .attr("cy", this.get_y(key))
            .attr("r", 2)
            .attr("fill", "red");
        
        this.svg.append("text")
            .attr("x", this.get_x(key, 10))
            .attr("y", this.get_y(key, 10))
            .text(this.get_text(key))
            .attr('text-anchor', this.get_anchor(key))
        
        if (path.length == 1) {
            this.draw_loop(lineGenerator, path);
            return
        }

        for (var i = 1; i < path.length; i++) {
            var coords: [number, number][] = []
            var mid, offset: number;
            [mid, offset] = this.get_curve_point(path[i-1], path[i]);
            coords[0] = [this.get_x(path[i-1]), this.get_y(path[i-1])];
            coords[1] = [this.get_x(mid, offset), this.get_y(mid, offset)];
            coords[2] = [this.get_x(path[i]), this.get_y(path[i])];
            var pathData: string = lineGenerator(coords) as string;
            this.svg.append('path')
                .attr('d', pathData)
                .attr('stroke-width', 1)
                .attr('fill', 'none')
                .attr('stroke', 'grey');
        }
    }

    draw_loop(lineGenerator: d3.Line<[number, number]>, path: number[]) {
        var coords: [number, number][] = []
        coords[0] = [this.get_x(path[0]), this.get_y(path[0])];
        coords[3] = coords[0]
        var mid = [this.get_x(path[0], -20), this.get_y(path[0], -20)];
        coords[1] = [mid[0] + 10, mid[1] - 10]
        coords[2] = [mid[0] + 10, mid[1] + 10]

        var pathData: string = lineGenerator(coords) as string;
            this.svg.append('path')
                .attr('d', pathData)
                .attr('stroke-width', 1)
                .attr('fill', 'none')
                .attr('stroke', 'grey');
    }

    get_curve_point(i: number, j: number): [number, number] {
        var left = (i + j)/ 2
        var right = (i + j + this.ticks)/2 % this.ticks
        var left_diff = Math.abs(left - i)
        var right_diff = Math.abs(right - i)
        var scale = d3.scaleLog()
                        .domain([0.5, this.ticks/2])
                        .range([25, this.r]);
        
        var [mid, diff] = left_diff < right_diff ? 
            [left, left_diff] : 
            [right, right_diff]
        
        return [mid, -scale(diff)]
    }

    get_x(i: number, offset: number = 0) {
        return this.cx + (this.r + offset) * Math.sin((i / this.ticks) * Math.PI*2);
    }

    get_y(i: number, offset: number = 0) {
        return this.cy + -(this.r + offset) * Math.cos((i / this.ticks) * Math.PI*2);
    }

    get_anchor(key: number) {
        if (key == 0 || key == this.ticks/2) {
            return "middle";
        } else if (key < this.ticks/2) {
            return "start";
        } else {
            return "end";
        }
    }

    get_text(key: number) {
        // Check text output under ~6 digits
        if (this.ticks > Math.pow(2,20)) {
            return d3.format(".2e")(key)
        }
        return key
    }

    build_chord() {
        this.svg = d3.select(this.root)
            .append('svg')
            .attr("font-size", 10)
            .attr("font-family", "sans-serif")
            .attr('height', this.height)
            .attr('width', this.width);
        
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
            .text((d) => { return this.get_text(d)} )
            .attr('text-anchor', (d) => { return this.get_anchor(d)})
    }
}