import * as ReactDOM from 'react-dom'
import * as React from 'react'
import {DHTRenderer, Props} from './dht_chord_renderer'

export function render(m: number, peers: number[], key?: number, path?: number[]) {
    var props: Props = {width: 400, height: 400, m: m, peers: peers}
    if (key && path) {
        props.key_id = key
        props.path = path
    }
    ReactDOM.render(
        React.createElement(DHTRenderer, props),
        document.getElementById("body")
    );
}