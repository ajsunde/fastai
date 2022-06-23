# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/14a_callback.data.ipynb (unless otherwise specified).


from __future__ import annotations


__all__ = ['CollectDataCallback', 'WeightedDL', 'PartialDL']

# Cell
#nbdev_comment from __future__ import annotations
from ..basics import *

# Cell
class CollectDataCallback(Callback):
    "Collect all batches, along with `pred` and `loss`, into `self.data`. Mainly for testing"
    def before_fit(self): self.data = L()
    def after_batch(self):
        self.data.append(self.learn.to_detach((self.xb,self.yb,self.pred,self.loss)))

# Cell
@delegates()
class WeightedDL(TfmdDL):
    "Weighted dataloader where `wgts` is used for the training set only"
    def __init__(self, dataset=None, bs=None, wgts=None, **kwargs):
        super().__init__(dataset=dataset, bs=bs, **kwargs)
        wgts = array([1.]*len(dataset) if wgts is None else wgts)
        self.wgts = wgts/wgts.sum()

    def get_idxs(self):
        if self.n==0: return []
        if not self.shuffle: return super().get_idxs()
        return list(np.random.choice(self.n, self.n, p=self.wgts))

# Cell
@patch
@delegates(Datasets.dataloaders)
def weighted_dataloaders(self:Datasets, wgts, bs=64, **kwargs):
    "Create a weighted dataloader `WeightedDL` with `wgts` for the training set"
    xtra_kwargs = [{}] * (self.n_subsets-1)
    return self.dataloaders(bs=bs, dl_type=WeightedDL, dl_kwargs=({'wgts':wgts}, *xtra_kwargs), **kwargs)

# Cell
@patch
@delegates(Datasets.weighted_dataloaders)
def weighted_dataloaders(self:DataBlock, source, wgts, bs=64, verbose:bool=False, **kwargs):
    "Create a weighted dataloader `WeightedDL` with `wgts` for the dataset"
    dss = self.datasets(source, verbose=verbose)
    if not hasattr(wgts, '__array__'): wgts = np.array(wgts)
    trn_wgts = wgts[dss.splits[0]]
    return dss.weighted_dataloaders(trn_wgts, bs=bs, after_batch=self.batch_tfms, after_item=self.item_tfms, **kwargs)

# Cell
@delegates()
class PartialDL(TfmdDL):
    "Select randomly partial quantity of data at each epoch"
    def __init__(self, dataset=None, bs=None, partial_n=None, **kwargs):
        super().__init__(dataset=dataset, bs=bs, **kwargs)
        self.partial_n = min(partial_n, self.n) if partial_n else None

    def get_idxs(self):
        if self.partial_n is None: return super().get_idxs()
        return list(np.random.choice(self.n, self.partial_n, replace=False))

    def __len__(self):
        if self.partial_n is None: return super().__len__()
        return self.partial_n//self.bs + (0 if self.drop_last or self.partial_n%self.bs==0 else 1)

# Cell
@patch
@delegates(Datasets.dataloaders)
def partial_dataloaders(self:FilteredBase, partial_n, bs=64, **kwargs):
    "Create a partial dataloader `PartialDL` for the training set"
    xtra_kwargs = [{}] * (self.n_subsets-1)
    return self.dataloaders(bs=bs, dl_type=PartialDL, dl_kwargs=({'partial_n':partial_n}, *xtra_kwargs), **kwargs)