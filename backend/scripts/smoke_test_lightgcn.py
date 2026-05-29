"""LightGCN 烟雾测试：跑 2 epoch 验证训练循环不报错。"""
import torch, time
from backend.scripts.train_lightgcn import (
    load_data, build_normalized_adj, adj_to_tensor, LightGCN,
    train_one_epoch, evaluate_val, CONFIG,
)

train_users, train_items, val_pairs, u2idx, i2idx, n_users, n_items = load_data(5)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

norm_adj = build_normalized_adj(train_users, train_items, n_users, n_items)
adj_t = adj_to_tensor(norm_adj, device)
model = LightGCN(n_users, n_items, CONFIG['embedding_dim'], CONFIG['num_layers']).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=CONFIG['lr'], weight_decay=CONFIG['weight_decay'])

for epoch in range(2):
    t0 = time.time()
    loss = train_one_epoch(model, adj_t, train_users, train_items, n_items, optimizer, CONFIG['batch_size'], device)
    model.propagate(adj_t)
    val = evaluate_val(model, val_pairs[:100], u2idx, i2idx, n_items, k=10, n_neg=99, device=device)
    print(f'Epoch {epoch}: loss={loss:.4f} R@10={val["recall"]:.4f} NDCG@10={val["ndcg"]:.4f} time={time.time()-t0:.0f}s')

print('SMOKE TEST PASSED — training loop works')
