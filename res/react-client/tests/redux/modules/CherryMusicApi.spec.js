import reducer, { initialState } from 'redux/modules/CherryMusicApi'

describe('(Redux) CherryMusicApi', () => {
  describe('(Reducer)', () => {
    it('sets up initial state', () => {
      expect(reducer(undefined, {})).to.eql(initialState)
    })
  })
})
