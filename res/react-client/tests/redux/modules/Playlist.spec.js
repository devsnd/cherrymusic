import reducer, { initialState } from 'redux/modules/Playlist'

describe('(Redux) Playlist', () => {
  describe('(Reducer)', () => {
    it('sets up initial state', () => {
      expect(reducer(undefined, {})).to.eql(initialState)
    })
  })
})
