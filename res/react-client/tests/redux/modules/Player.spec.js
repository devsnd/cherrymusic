import reducer, { initialState } from 'redux/modules/Player'

describe('(Redux) Player', () => {
  describe('(Reducer)', () => {
    it('sets up initial state', () => {
      expect(reducer(undefined, {})).to.eql(initialState)
    })
  })
})
