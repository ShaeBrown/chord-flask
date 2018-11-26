import { DHTRenderer } from './dht_chord_renderer'
import * as React from "react";
import * as ReactDOM from "react-dom";

ReactDOM.render(
    React.createElement(DHTRenderer, {m: 4, peers: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]}),
    document.getElementById("body")
);