import { defineStore } from 'pinia'

import { BOX_DEFAULTS, BOX_MODE, PARAMS_DEFAULTS } from '../utils/constants'

function defaults() {
  return { ...BOX_DEFAULTS, ...PARAMS_DEFAULTS }
}

export const useDockStore = defineStore('dock', {
  state: () => ({
    params: defaults(),
    boxMode: BOX_MODE.MANUAL
  }),

  getters: {
    box3d(state) {
      return {
        center: {
          x: state.params.center_x,
          y: state.params.center_y,
          z: state.params.center_z
        },
        size: {
          x: state.params.size_x,
          y: state.params.size_y,
          z: state.params.size_z
        }
      }
    }
  },

  actions: {
    setParams(params) {
      this.params = { ...this.params, ...params }
    },

    setBoxMode(mode) {
      this.boxMode = mode
    },

    setBox({ center, size }) {
      this.params = {
        ...this.params,
        center_x: Number(center.x),
        center_y: Number(center.y),
        center_z: Number(center.z),
        size_x: Number(size.x),
        size_y: Number(size.y),
        size_z: Number(size.z)
      }
    },

    setCenter(center) {
      this.params = {
        ...this.params,
        center_x: Number(center.x),
        center_y: Number(center.y),
        center_z: Number(center.z)
      }
    },

    applyPocket(pocket) {
      this.params = {
        ...this.params,
        center_x: pocket.center_x,
        center_y: pocket.center_y,
        center_z: pocket.center_z,
        size_x: pocket.size_x,
        size_y: pocket.size_y,
        size_z: pocket.size_z
      }
      this.boxMode = BOX_MODE.AUTO
    },

    applyLoadedParams(params) {
      this.params = { ...defaults(), ...(params || {}) }
    },

    reset() {
      this.params = defaults()
      this.boxMode = BOX_MODE.MANUAL
    }
  }
})
